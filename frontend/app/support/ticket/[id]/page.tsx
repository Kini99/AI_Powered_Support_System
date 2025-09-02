"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { getMessageBackgroundColor, Message, TicketDetail } from "@/types";
import { formatTimestamp, getStatusColor } from "@/utils";
import { Bookmark, RotateCcw } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface TicketDetailResponse {
  ticket: TicketDetail;
  conversations: Message[];
}

export default function TicketDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [ticket, setTicket] = useState<TicketDetailResponse | null>(null);
  const [selectedRating, setSelectedRating] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchTicketDetail = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE}/v1/tickets/${params.id}`,
          {
            credentials: "include",
          }
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: TicketDetailResponse = await response.json();
        setTicket(data);
        setSelectedRating(data.ticket.rating || null);
      } catch (error) {
        console.error("Failed to fetch ticket details:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTicketDetail();
  }, [params.id]);

  const handleRating = async (rating: number) => {
    setSelectedRating(rating);

    // Mock API call to update rating
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/v1/tickets/${params.id}/rate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({ rating }),
        }
      );
    } catch (error) {
      console.error("Failed to submit rating:", error);
    }
  };

  const handleReopenTicket = async () => {
    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/v1/tickets/${params.id}/reopen`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      // Refresh the page or update state
      router.refresh();
    } catch (error) {
      console.error("Failed to reopen ticket:", error);
    }
  };

  const ratingEmojis = ["😠", "😞", "😐", "😊", "😍"];

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp.endsWith('Z') ? timestamp : timestamp + 'Z');
    if (isNaN(date.getTime())) {
      console.error("Invalid timestamp received:", timestamp);
      return "Invalid Date";
    }
    return new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata",
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(date);
  };

  const formatSenderName = (email: string | undefined, role: string) => {
    if (email) {
      const name = email.split("@")[0];
      return name.charAt(0).toUpperCase() + name.slice(1);
    }
    return role.charAt(0).toUpperCase() + role.slice(1);
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="p-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!ticket) {
    return (
      <DashboardLayout>
        <div className="p-6">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900">
              Ticket not found
            </h2>
            <p className="text-gray-600 mt-2">
              The ticket you're looking for doesn't exist.
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-semibold text-gray-900">
              {ticket.ticket.title}
            </h1>
            <Badge className={getStatusColor(ticket.ticket.status)}>
              {ticket.ticket.status === "Admin Action Required"
                ? "WORK IN PROGRESS"
                : ticket.ticket.status.toUpperCase()}
            </Badge>
          </div>

          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              <Bookmark className="h-4 w-4 mr-2" />
              BOOKMARK
            </Button>

            {ticket.ticket.status === "Resolved" && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleReopenTicket}
                className="text-blue-600 border-blue-600 hover:bg-blue-50"
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                REOPEN TICKET
              </Button>
            )}
          </div>
        </div>

        {/* Ticket Info */}
        <div className="mb-6 text-sm text-gray-600">
          <span>Support related to: </span>
          <span className="font-medium">{ticket.ticket.category}</span>
          {ticket.ticket.subcategory_data?.activity && (
            <>
              <span className="mx-2">•</span>
              <span>Activity: </span>
              <span className="font-medium">
                {ticket.ticket.subcategory_data?.activity || "N/A"}
              </span>
            </>
          )}
        </div>

        {/* Messages */}
        <div className="space-y-6 mb-8">
          {ticket.conversations.map((message, index) => (
            <Card
              key={message.id}
              className={getMessageBackgroundColor(message.sender_role)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center space-x-3">
                  <Avatar className="h-8 w-8">
                    <AvatarImage
                      src={
                        message.sender_email
                          ? `/placeholder.svg?height=32&width=32`
                          : undefined
                      }
                    />
                    <AvatarFallback className="bg-green-100 text-green-700">
                      {message.sender_email
                        ? message.sender_email
                            .split(" ")
                            .map((n) => n[0])
                            .join("")
                        : message.sender_role.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium text-gray-900">
                      {formatSenderName(
                        message.sender_email,
                        message.sender_role
                      )}
                    </div>
                    {message.sender_role === "admin" &&
                      ticket.ticket.status === "Resolved" &&
                      index === ticket.conversations.length - 1 && (
                        <Badge className="bg-orange-100 text-orange-800 text-xs mt-1">
                          TICKET RESOLVED
                        </Badge>
                      )}
                  </div>
                  <div className="flex-1"></div>
                  <div className="text-sm text-gray-500">
                    {formatTimestamp(message.timestamp)}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="text-gray-700 whitespace-pre-line">
                  {message.message}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {ticket.ticket.status !== "Resolved" && (
          <div className="mt-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Send a Message
            </h3>
            <textarea
              className="w-full p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type your message here..."
              rows={4}
            ></textarea>
            <input
              type="file"
              multiple
              className="mt-3 p-2 border rounded-lg"
              id="attachment-input"
            />
            <Button
              className="mt-3 bg-blue-600 text-white hover:bg-blue-700"
              onClick={async () => {
                const messageInput = document.querySelector("textarea");
                const attachmentInput = document.getElementById(
                  "attachment-input"
                ) as HTMLInputElement;
                const message = messageInput?.value;
                const attachments = Array.from(
                  attachmentInput?.files || []
                ).map((file) => file.name); // Just sending names for now

                if (message || attachments.length > 0) {
                  try {
                    const response = await fetch(
                      `${process.env.NEXT_PUBLIC_API_BASE}/v1/tickets/${params.id}/messages`,
                      {
                        method: "POST",
                        headers: {
                          "Content-Type": "application/json",
                        },
                        credentials: "include",
                        body: JSON.stringify({ message, attachments }),
                      }
                    );
                    if (!response.ok) {
                      throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const newMessage = await response.json();
                    setTicket((prevTicket) => {
                      if (!prevTicket) return null;
                      return {
                        ...prevTicket,
                        conversations: [
                          ...prevTicket.conversations,
                          newMessage,
                        ],
                      };
                    });
                    if (messageInput) {
                      messageInput.value = ""; // Clear the textarea
                    }
                    if (attachmentInput) {
                      attachmentInput.value = ""; // Clear the file input
                    }
                  } catch (error) {
                    console.error("Failed to send message:", error);
                  }
                }
              }}
            >
              Send Message
            </Button>
          </div>
        )}

        {/* Rating Section */}
        {ticket.ticket.status === "Resolved" && (
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Rating & Feedback
              </h3>
              <div className="mb-4">
                <p className="text-sm text-gray-600 mb-3">
                  How happy are you with the assistance?
                </p>
                <div className="flex space-x-2">
                  {ratingEmojis.map((emoji, index) => {
                    const rating = index + 1;
                    return (
                      <button
                        key={rating}
                        onClick={() => handleRating(rating)}
                        className={`text-2xl p-2 rounded-lg transition-all ${
                          selectedRating === rating
                            ? "bg-blue-100 scale-110"
                            : "hover:bg-gray-100 hover:scale-105"
                        }`}
                      >
                        {emoji}
                      </button>
                    );
                  })}
                </div>
              </div>

              {selectedRating && (
                <div className="text-sm text-gray-600">
                  Thank you for your feedback! You rated this resolution{" "}
                  {selectedRating} out of 5.
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
