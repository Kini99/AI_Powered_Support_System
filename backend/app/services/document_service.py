# backend/app/services/document_service.py

import os
import uuid
import asyncio
import logging
import tempfile
import mimetypes
from typing import List, Dict, Any, Optional
import io
import pandas as pd
from fastapi import UploadFile
from pinecone import Pinecone, Index
from bson.objectid import ObjectId
import gridfs
import functools
from unstructured.partition.auto import partition
from unstructured.chunking.title import chunk_by_title
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.app.core.config import settings
from backend.app.db.base import get_mongodb

logger = logging.getLogger(__name__)


async def run_in_threadpool(func, *args, **kwargs):
    """Runs a synchronous function in a separate thread to avoid blocking."""
    loop = asyncio.get_running_loop()
    func_with_args = functools.partial(func, *args, **kwargs)
    return await loop.run_in_executor(None, func_with_args)


class DocumentService:
    """
    Manages document ingestion, storage, deletion, and searching across
    multiple dedicated Pinecone indices based on document category, using
    unstructured.io for document processing.
    """
    def __init__(self):
        self.mongodb = get_mongodb()
        self.gridfs = gridfs.GridFS(self.mongodb)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        self.pinecone_indices: Dict[str, Index] = {}
        if settings.PINECONE_API_KEY:
            self.pinecone = Pinecone(api_key=settings.PINECONE_API_KEY)
            for category, index_name in settings.PINECONE_INDEX_MAP.items():
                try:
                    self.pinecone_indices[category] = self.pinecone.Index(index_name)
                    print(f"Successfully connected to Pinecone index: '{index_name}' for category '{category}'")
                except Exception as e:
                    print(f"Failed to connect to Pinecone index '{index_name}': {e}")
        else:
            self.pinecone = None
            print("PINECONE_API_KEY not set. Pinecone operations will be skipped.")

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.collection_map = settings.MONGO_COLLECTION_MAP
        self.valid_categories = self.collection_map.keys()

    def _get_index(self, category: str) -> Optional[Index]:
        """Safely retrieves the Pinecone index for a given category."""
        index = self.pinecone_indices.get(category)
        if not index:
            print(f"No Pinecone index configured for category '{category}'. Skipping operation.")
        return index

    async def _process_and_store_excel_qa(self, file_content: bytes, filename: str, doc_id: str, categories: List[str],
                                         course_categories: Optional[List[str]] = None, course_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Processes a Q&A Excel file row by row, embedding the 'message'
        and storing the 'Potential response' in the vector's metadata.
        This now supports storing in multiple categories.
        """
        print("--- Processing file using dedicated Excel Q&A logic for multiple categories ---")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name

            df = await run_in_threadpool(pd.read_excel, temp_path)
            os.unlink(temp_path)

            if "message" not in df.columns or "Potential response" not in df.columns:
                raise ValueError("Excel file must contain 'message' and 'Potential response' columns for Q&A processing.")

            df = df[["message", "Potential response"]].dropna().reset_index()
            if df.empty:
                raise ValueError("No valid rows found in the Excel file.")

            messages_to_embed = df["message"].tolist()
            embeddings = await self.embeddings.aembed_documents(messages_to_embed)

            # Store the physical file once
            mime_type, _ = mimetypes.guess_type(filename)
            gridfs_id = await run_in_threadpool(self.gridfs.put, file_content, filename=filename, content_type=mime_type)

            total_vectors_stored = 0
            for category in categories:
                vectors = []
                for index, row in df.iterrows():
                    vector = {
                        "id": f"{doc_id}_row_{index}_{category}", # Ensure unique ID per category
                        "values": embeddings[index],
                        "metadata": {
                            "doc_id": doc_id,
                            "category": category,
                            "filename": filename,
                            "text_snippet": row["message"],
                            "potential_response": row["Potential response"],
                            "course_category": course_categories,
                            "course_names": course_names or [],
                        }
                    }
                    vectors.append(vector)

                pinecone_index = self._get_index(category)
                if pinecone_index:
                    await run_in_threadpool(pinecone_index.upsert, vectors=vectors, batch_size=100)
                    if total_vectors_stored == 0:
                        total_vectors_stored = len(vectors)
                    print(f"Stored {len(vectors)} Q&A pairs in Pinecone for doc {doc_id} in category '{category}'")

                collection_name = self.collection_map[category]
                document_metadata = {
                    "doc_id": doc_id, "file_name": filename, "gridfs_id": str(gridfs_id),
                    "category": category, "chunk_count": len(vectors),
                    "course_category": course_categories,
                    "course_names": course_names or [],
                    "metadata": {"file_type": mime_type, "file_size": len(file_content)}
                }
                collection = self.mongodb[collection_name]
                await run_in_threadpool(collection.insert_one, document_metadata)
                print(f"Stored metadata for Excel doc {doc_id} in MongoDB collection '{collection_name}'.")

            return {"document_id": doc_id, "items_created": total_vectors_stored, "categories": categories}

        except Exception as e:
            print(f"Excel Q&A processing error for '{filename}': {e}")
            raise e

    async def upload_document(self, file: UploadFile, categories: List[str], course_categories: Optional[List[str]] = None, 
                             course_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Upload, process, and index a document into multiple specified category indices."""
        for category in categories:
            if category not in self.collection_map:
                raise ValueError(f"Invalid category '{category}'. Must be one of: {list(self.collection_map.keys())}")

        try:
            doc_id = str(uuid.uuid4())
            content = await file.read()
            filename = file.filename
            chunk_texts = []
            metadata_list = None

            is_excel_qa = False
            if filename.endswith(('.xlsx', '.xls')):
                try:
                    df_peek = pd.read_excel(io.BytesIO(content))
                    if "message" in df_peek.columns and "Potential response" in df_peek.columns:
                        is_excel_qa = True
                except Exception:
                    pass

            if is_excel_qa:
                return await self._process_and_store_excel_qa(content, filename, doc_id, categories, course_categories, course_names)

            elif filename.endswith('.csv'):
                print(f"Processing '{filename}' as a CSV file.")
                try:
                    df = pd.read_csv(io.BytesIO(content))
                except UnicodeDecodeError:
                    print("Default CSV decoding failed, trying UTF-8.")
                    df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
                text_content = df.to_string(index=False)
                chunk_texts = self.text_splitter.split_text(text_content)
            else:
                print(f"Processing '{filename}' with unstructured.io.")
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                    temp_file.write(content)
                    temp_path = temp_file.name
                try:
                    elements = await run_in_threadpool(partition, filename=temp_path, content_type=file.content_type, strategy="fast")
                    chunk_elements = await run_in_threadpool(chunk_by_title, elements, max_characters=1000, new_after_n_chars=800)
                    chunk_texts = [c.text for c in chunk_elements]
                    metadata_list = [c.metadata.to_dict() for c in chunk_elements]
                finally:
                    os.unlink(temp_path)

            if not chunk_texts:
                raise ValueError("No text content could be extracted from the file.")

            final_mime_type = file.content_type or 'application/octet-stream'
            gridfs_id = await run_in_threadpool(self.gridfs.put, content, filename=filename, content_type=final_mime_type)

            # Loop through each category to store metadata and vectors
            for category in categories:
                document = {
                    "doc_id": doc_id, "file_name": filename, "gridfs_id": str(gridfs_id),
                    "category": category, "chunk_count": len(chunk_texts),
                    "course_category": course_categories,
                    "course_names": course_names or [],
                    "metadata": {"file_type": final_mime_type, "file_size": len(content)}
                }
                collection_name = self.collection_map[category]
                collection = self.mongodb[collection_name]
                await run_in_threadpool(collection.insert_one, document)

                pinecone_index = self._get_index(category)
                if pinecone_index:
                    await self._store_in_pinecone(pinecone_index, doc_id, chunk_texts, category, filename, metadata_list, course_categories, course_names)
                
                print(f"Document '{filename}' stored for category '{category}'")

            return {"document_id": doc_id, "items_created": len(chunk_texts), "categories": categories}

        except Exception as e:
            print(f"Upload error for '{file.filename}': {e}")
            raise e

    async def _store_in_pinecone(self, index: Index, doc_id: str, chunks: List[str], category: str, filename: str, 
                               metadata_list: Optional[List[Dict]] = None, course_categories: Optional[List[str]] = None, 
                               course_names: Optional[List[str]] = None):
        """Asynchronously embed and store document chunks in a specific Pinecone index."""
        try:
            embeddings = await self.embeddings.aembed_documents(chunks)
            vectors = []
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                vector_metadata = {
                    "doc_id": doc_id,
                    "category": category,
                    "filename": filename,
                    "text_snippet": chunk_text[:1000],
                    "course_category": course_categories,
                    "course_names": course_names or [],
                }
                if metadata_list and i < len(metadata_list):
                    unstructured_meta = metadata_list[i]
                    page_number = unstructured_meta.get("page_number")
                    if page_number is not None: vector_metadata["page_number"] = page_number
                    element_type = unstructured_meta.get("category")
                    if element_type is not None: vector_metadata["element_type"] = element_type
                
                vector = {
                    "id": f"{doc_id}_{category}_chunk_{i}", # Unique ID per chunk per category
                    "values": embedding,
                    "metadata": vector_metadata
                }
                vectors.append(vector)

            await run_in_threadpool(index.upsert, vectors=vectors, batch_size=100)
            index_name = settings.PINECONE_INDEX_MAP.get(category, "unknown")
            logger.info(f"Stored {len(vectors)} vectors in Pinecone index '{index_name}' for doc {doc_id}")

        except Exception as e:
            index_name = settings.PINECONE_INDEX_MAP.get(category, "unknown")
            logger.error(f"Pinecone storage error for index '{index_name}': {e}")
            raise e
           
    async def delete_document(self, doc_id: str):
        """
        Deletes a document from ALL MongoDB collections and its vectors 
        from corresponding Pinecone indices.
        """
        try:
            deleted_count = 0
            categories_deleted_from = []

            for category, collection_name in self.collection_map.items():
                collection = self.mongodb[collection_name]
                doc = await run_in_threadpool(collection.find_one_and_delete, {"doc_id": doc_id})
                if doc:
                    deleted_count += 1
                    categories_deleted_from.append(category)
                    # Only delete from GridFS on the first hit to avoid errors
                    if deleted_count == 1 and 'gridfs_id' in doc:
                        gridfs_object_id = ObjectId(doc['gridfs_id'])
                        await run_in_threadpool(self.gridfs.delete, gridfs_object_id)
                    
                    print(f"Deleted metadata for {doc_id} from MongoDB collection '{collection_name}'.")

            if deleted_count == 0:
                raise ValueError(f"Document {doc_id} not found in any collection.")

            # Delete from all relevant pinecone indices
            for category in categories_deleted_from:
                index = self._get_index(category)
                if index:
                    index_name = settings.PINECONE_INDEX_MAP[category]
                    await run_in_threadpool(index.delete, filter={"doc_id": doc_id})
                    print(f"Deleted vectors for {doc_id} from Pinecone index '{index_name}'.")

        except Exception as e:
            print(f"Deletion error for doc {doc_id}: {e}")
            raise e

    # The search_documents and list_documents methods do not require changes for this request.
    # ... (rest of the file is unchanged)
    async def search_documents(self, query: str, categories: Optional[List[str]] = None, top_k: int = 5, 
                             course_category: Optional[str] = None, course_name: Optional[str] = None) -> List[Dict[str, Any]]:
        # This method remains unchanged.
        """Search for documents by embedding a query and searching one or more Pinecone indices."""
        if not self.pinecone:
            print("Pinecone is not configured. Cannot perform search.")
            return []

        indices_to_search = {}
        target_categories = categories or self.pinecone_indices.keys()
        for cat in target_categories:
            if cat in self.pinecone_indices:
                indices_to_search[cat] = self.pinecone_indices[cat]

        if not indices_to_search:
            print(f"No valid indices found for specified categories: {categories}")
            return []

        try:
            query_embedding = await self.embeddings.aembed_query(query)

            async def query_index(index: Index):
                query_filter = {}
                if course_category and course_name:
                    query_filter = {
                        "$and": [
                            {"course_category": {"$eq": course_category}},
                            {"course_names": {"$in": [course_name]}}
                        ]
                    }
                elif course_category:
                    query_filter = {"course_category": {"$eq": course_category}}
                
                return await run_in_threadpool(
                    index.query,
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True,
                    filter=query_filter if query_filter else None
                )

            tasks = [query_index(index) for index in indices_to_search.values()]
            query_results = await asyncio.gather(*tasks)

            all_matches = []
            for result in query_results:
                all_matches.extend(result.get('matches', []))

            sorted_matches = sorted(all_matches, key=lambda x: x.get('score', 0), reverse=True)

            final_results = []
            for match in sorted_matches[:top_k]:
                metadata = match.get('metadata', {})
                final_results.append({
                    "score": match.get('score'),
                    "category": metadata.get('category'),
                    "filename": metadata.get('filename'),
                    "doc_id": metadata.get('doc_id'),
                    "text_snippet": metadata.get('text_snippet'),
                    "potential_response": metadata.get('potential_response'),
                    "page_number": metadata.get('page_number'),
                    "element_type": metadata.get('element_type')
                })

            return final_results

        except Exception as e:
            print(f"Error during document search for query '{query}': {e}")
            raise e

    async def list_documents(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        # This method remains unchanged.
        """Lists document metadata from MongoDB."""
        documents = []
        collections_to_search = []
        if category:
            if category in self.collection_map:
                collections_to_search.append(self.collection_map[category])
        else:
            collections_to_search = self.collection_map.values()

        if not collections_to_search:
            return []

        async def fetch_all_docs(collection_name: str):
            collection = self.mongodb[collection_name]
            docs = []
            cursor = collection.find({}, {"content": 0})
            for doc in await run_in_threadpool(list, cursor):
                doc["_id"] = str(doc["_id"])
                docs.append(doc)
            return docs

        tasks = [fetch_all_docs(name) for name in collections_to_search]
        results = await asyncio.gather(*tasks)
        for doc_list in results:
            documents.extend(doc_list)

        return documents