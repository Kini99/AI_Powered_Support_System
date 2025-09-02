"use client";

import AdminDashboardLayout from "@/components/admin-dashboard-layout";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useEffect, useRef, useState } from "react";

interface DocumentRecord {
  _id: string;
  doc_id: string;
  file_name: string;
  upload_date: string;
  category?: string;
  course_category?: string[];
  course_names?: string[];
}

interface CategoryGuide {
  category: string;
  label: string;
  subcategories: Array<{ name: string; description?: string }>;
}

const courseCategories = {
  Management: [
    "Product Management with Generative & Agentic AI",
    "Certification Program in Business Analytics with Gen & Agentic AI",
    "Product Management and Agentic AI",
    "Advanced Project Management & Strategic Leadership",
    "Entrepreneurship Launchpad",
    "Certificate Program in Entrepreneurship and Start Up Mastery",
    "Certificate program in Smart Supply Chain Management",
    "Entrepreneurship & Leadership Toolkit Program",
    "Business Analytics",
  ],
  "AI/ML": [
    "Minor in AI",
    "Artificial Intelligence and Machine Learning",
    "Specialized Program in Artificial Intelligence & Machine Learning with Drone Tech",
    "Credit-Linked program in Artificial Intelligence & Machine Learning",
  ],
  "Data Science": [
    "Credit-Linked Program in Data Science",
    "Minor in Artificial Intelligence & Data Science",
    "Data Science",
  ],
  Marketing: [
    "Digital Marketing with Applied AI",
    "HR Analytics with Gen AI for HR Professionals",
    "Digital Marketing",
    "Digital Marketing & Analytics",
    "Gen AI Product Launchpad",
  ],
  "Software Development": [
    "Cyber Security and Ethical Hacking with applied AI",
    "New Age Software Engineering Program",
    "Credit-Linked program in CSE & AI",
    "IIT Mandi Cybersecurity",
    "Software development 2.0 with emerging tech",
    "Software Development",
  ],
  Electronics: ["Minor in Embedded Systems"],
};

const categoryGuides: CategoryGuide[] = [
  {
    category: "program_details_documents",
    label: "Program Details",
    subcategories: [
      { name: "Course Query" },
      { name: "Attendance/Counselling Support" },
      { name: "Leave", description: "Leave policies" },
      {
        name: "Late Evaluation Submission",
        description: "Submission policies",
      },
      {
        name: "Missed Evaluation Submission",
        description: "Evaluation policies",
      },
      { name: "Withdrawal", description: "Withdrawal policies" },
      {
        name: "Other Course Query",
        description: "Details of Course Curriculum",
      },
    ],
  },
  {
    category: "curriculum_documents",
    label: "Curriculum Documents",
    subcategories: [
      { name: "Evaluation Score" },
      { name: "MAC", description: "Masai Additional Curriculum" },
      { name: "Revision", description: "Course content revision" },
    ],
  },
  {
    category: "qa_documents",
    label: "FAQ",
    subcategories: [
      { name: "Product Support" },
      { name: "NBFC/ISA", description: "Financial FAQs" },
      { name: "Feedback" },
      { name: "Referral" },
      { name: "Personal Query" },
      { name: "Code Review" },
      { name: "Placement Support - Placements" },
      { name: "Offer Stage- Placements" },
      { name: "ISA/EMI/NBFC/Glide Related - Placements" },
      { name: "Session Support - Placement" },
      { name: "IA Support", description: "Technical support from IA" },
    ],
  },
];

export default function AdminDocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [selectedCourseCategories, setSelectedCourseCategories] = useState<
    string[]
  >([]);
  const [selectedCourseNames, setSelectedCourseNames] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function fetchDocuments() {
    setIsLoading(true);
    setError("");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/v1/admin/documents`,
        { credentials: "include" }
      );
      if (!res.ok) throw new Error("Failed to fetch documents");
      const data = await res.json();
      setDocuments(Array.isArray(data.documents) ? data.documents : []);
    } catch (err) {
      setError("Error loading documents");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchDocuments();
  }, []);

  async function handleDelete(docId: string) {
    if (
      !window.confirm(
        "Are you sure you want to delete this document? This will remove it from all associated categories."
      )
    )
      return;
    setIsLoading(true);
    setError("");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/v1/admin/documents/${docId}`,
        { method: "DELETE", credentials: "include" }
      );
      if (!res.ok) throw new Error("Delete failed");
      fetchDocuments();
    } catch (err) {
      setError("Failed to delete document");
      setIsLoading(false);
    }
  }

  async function handleUpload(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (
      !fileInputRef.current?.files?.[0] ||
      !selectedCategory || // Changed from selectedCategories.length === 0
      selectedCourseCategories.length === 0
    ) {
      setError(
        "Please select a document category, at least one course category, and upload a file."
      );
      return;
    }
    setUploading(true);
    setError("");
    try {
      const file = fileInputRef.current.files[0];
      const formData = new FormData();
      formData.append("file", file);
      // Send the single category as an array with one item
      formData.append("categories", JSON.stringify([selectedCategory]));
      formData.append(
        "course_categories",
        JSON.stringify(selectedCourseCategories)
      );
      formData.append("course_names", JSON.stringify(selectedCourseNames));

      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/v1/admin/documents/upload`,
        { method: "POST", body: formData, credentials: "include" }
      );
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Upload failed");
      }

      fileInputRef.current.value = "";
      setSelectedCategory("");
      setSelectedCourseCategories([]);
      setSelectedCourseNames([]);
      fetchDocuments();
    } catch (err: any) {
      setError(`Failed to upload document: ${err.message}`);
    } finally {
      setUploading(false);
    }
  }

  const handleCourseCategoryToggle = (courseCategory: string) => {
    const coursesInCat =
      courseCategories[courseCategory as keyof typeof courseCategories] || [];
    const isCurrentlySelected =
      selectedCourseCategories.includes(courseCategory);

    setSelectedCourseCategories((prev) =>
      isCurrentlySelected
        ? prev.filter((c) => c !== courseCategory)
        : [...prev, courseCategory]
    );

    setSelectedCourseNames((prevNames) => {
      if (isCurrentlySelected) {
        // Remove courses of the unselected category
        return prevNames.filter((name) => !coursesInCat.includes(name));
      } else {
        // Add courses of the newly selected category (avoiding duplicates)
        return [...new Set([...prevNames, ...coursesInCat])];
      }
    });
  };

  const handleCourseNameToggle = (courseName: string) => {
    // Determine the new list of selected course names after the toggle.
    const newSelectedCourseNames = selectedCourseNames.includes(courseName)
      ? selectedCourseNames.filter((name) => name !== courseName)
      : [...selectedCourseNames, courseName];

    // Update the state for the selected course names.
    setSelectedCourseNames(newSelectedCourseNames);

    // This logic runs only when a course is being UNSELECTED.
    if (selectedCourseNames.includes(courseName)) {
      // Find which course category this course belongs to.
      let parentCategory: string | undefined;
      for (const [category, courses] of Object.entries(courseCategories)) {
        if ((courses as string[]).includes(courseName)) {
          parentCategory = category;
          break;
        }
      }

      // If a parent category was found, check if any other courses from it are still selected.
      if (parentCategory) {
        const coursesInParentCat =
          courseCategories[parentCategory as keyof typeof courseCategories];

        const isAnyOtherCourseSelected = coursesInParentCat.some((cn) =>
          newSelectedCourseNames.includes(cn)
        );

        // If no other courses from this category are selected, unselect the category itself.
        if (!isAnyOtherCourseSelected) {
          setSelectedCourseCategories((prevCategories) =>
            prevCategories.filter((cat) => cat !== parentCategory)
          );
        }
      }
    }
  };

  const availableCoursesForSelection = selectedCourseCategories.flatMap(
    (cat) => courseCategories[cat as keyof typeof courseCategories] || []
  );

  return (
    <AdminDashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">
          Document Management
        </h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Upload Document</CardTitle>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="text-red-600 mb-4 p-3 bg-red-50 rounded-md">
                  {error}
                </div>
              )}
              <form onSubmit={handleUpload} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Document Categories
                  </label>
                  <Select
                    value={selectedCategory}
                    onValueChange={setSelectedCategory}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select a category" />
                    </SelectTrigger>
                    <SelectContent>
                      {categoryGuides.map((guide) => (
                        <SelectItem key={guide.category} value={guide.category}>
                          {guide.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">
                    Course Categories
                  </label>
                  <div className="border rounded p-3 space-y-2">
                    {Object.keys(courseCategories).map((category) => (
                      <div
                        key={category}
                        className="flex items-center space-x-2"
                      >
                        <input
                          type="checkbox"
                          id={`course-cat-${category}`}
                          checked={selectedCourseCategories.includes(category)}
                          onChange={() => handleCourseCategoryToggle(category)}
                          className="rounded border-gray-300"
                        />
                        <label
                          htmlFor={`course-cat-${category}`}
                          className="text-sm cursor-pointer flex-1"
                        >
                          {category}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                {selectedCourseCategories.length > 0 && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Course Names</label>
                    <div className="border rounded p-3 max-h-40 overflow-y-auto space-y-2">
                      {availableCoursesForSelection.map((courseName) => (
                        <div
                          key={courseName}
                          className="flex items-center space-x-2"
                        >
                          <input
                            type="checkbox"
                            id={`course-${courseName}`}
                            checked={selectedCourseNames.includes(courseName)}
                            onChange={() => handleCourseNameToggle(courseName)}
                            className="rounded border-gray-300"
                          />
                          <label
                            htmlFor={`course-${courseName}`}
                            className="text-sm cursor-pointer flex-1"
                          >
                            {courseName}
                          </label>
                        </div>
                      ))}
                    </div>
                    <div className="text-xs text-gray-500">
                      {selectedCourseNames.length} of{" "}
                      {availableCoursesForSelection.length} courses from
                      selected categories are chosen.
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-sm font-medium">Document File *</label>
                  <input
                    type="file"
                    ref={fileInputRef}
                    required
                    className="w-full border rounded bg-white px-2 py-1.5 text-sm"
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full"
                  disabled={
                    uploading ||
                    !selectedCategory ||
                    selectedCourseCategories.length === 0
                  }
                >
                  {uploading ? "Uploading..." : "Upload Document"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Category Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[50vh]">
                <Accordion type="single" collapsible className="w-full">
                  {categoryGuides.map((guide) => (
                    <AccordionItem key={guide.category} value={guide.category}>
                      <AccordionTrigger className="text-lg font-semibold hover:no-underline">
                        {guide.label}
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="grid">
                          {guide.subcategories.map((sub, idx) => (
                            <div key={idx} className="p-2">
                              <div className="font-medium text-gray-900">
                                {sub.name}{" "}
                                {sub.description ? `(${sub.description})` : ""}
                              </div>
                            </div>
                          ))}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card className="md:col-span-2">
            <CardHeader>
              <CardTitle>Uploaded Documents</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div>Loading...</div>
              ) : (
                <ul className="space-y-2">
                  {documents.length === 0 && (
                    <li className="text-gray-400">No documents found.</li>
                  )}
                  {documents.map((doc) => (
                    <li
                      key={doc._id}
                      className="flex items-center justify-between bg-gray-50 rounded p-3"
                    >
                      <div className="space-y-1">
                        <div className="font-medium">{doc.file_name}</div>
                        <div className="flex flex-col space-y-1 text-sm text-gray-500">
                          <div className="flex items-center space-x-2">
                            <span>
                              {doc.upload_date
                                ? new Date(doc.upload_date).toLocaleString()
                                : ""}
                            </span>
                            {doc.category && (
                              <>
                                <span>•</span>
                                <span>
                                  {categoryGuides.find(
                                    (g) => g.category === doc.category
                                  )?.label || doc.category}
                                </span>
                              </>
                            )}
                          </div>
                          {doc.course_category &&
                            doc.course_category.length > 0 && (
                              <div className="flex items-center space-x-2 flex-wrap">
                                <span className="font-medium text-blue-600">
                                  Course Cats:
                                </span>
                                <span>{doc.course_category.join(", ")}</span>
                                {doc.course_names &&
                                  doc.course_names.length > 0 && (
                                    <>
                                      <span>•</span>
                                      <span>
                                        {doc.course_names.length} course
                                        {doc.course_names.length !== 1
                                          ? "s"
                                          : ""}
                                      </span>
                                    </>
                                  )}
                              </div>
                            )}
                        </div>
                      </div>
                      <Button
                        type="button"
                        size="sm"
                        variant="destructive"
                        onClick={() => handleDelete(doc.doc_id)}
                        disabled={isLoading}
                      >
                        Delete
                      </Button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminDashboardLayout>
  );
}
