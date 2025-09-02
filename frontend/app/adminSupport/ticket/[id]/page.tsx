"use client";

import AdminDashboardLayout from "@/components/admin-dashboard-layout";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { getMessageBackgroundColor, Message, TicketDetail } from "@/types";
import { formatTimestamp, getStatusColor } from "@/utils";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

interface TicketDetailResponse {
  ticket: TicketDetail;
  conversations: Message[];
}

export default function AdminTicketDetailPage() {
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
      <AdminDashboardLayout>
        <div className="p-6 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </AdminDashboardLayout>
    );
  }

  if (!ticket) {
    return (
      <AdminDashboardLayout>
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
      </AdminDashboardLayout>
    );
  }

  return (
    <AdminDashboardLayout>
      <div className="p-6 max-w-4xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-semibold text-gray-900">
              {ticket.ticket.title}
            </h1>
            <Badge className={getStatusColor(ticket.ticket.status)}>
              {ticket.ticket.status === "Student Action Required"
                ? "WORK IN PROGRESS"
                : ticket.ticket.status.toUpperCase()}
            </Badge>
            {ticket.ticket.status !== 'Resolved' &&   <Button
              className="ml-2 bg-green-600 text-white hover:bg-green-700"
              onClick={async () => {
                const messageInput = document.querySelector("textarea");
                const message = messageInput?.value || "Ticket resolved.";

                try {
                  const formData = new FormData();
                  formData.append('message', message);

                  const response = await fetch(
                    `${process.env.NEXT_PUBLIC_API_BASE}/v1/admin/tickets/${params.id}/resolve`,
                    {
                      method: "POST",
                      credentials: "include",
                      body: formData,
                    }
                  );
                  if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                  }
                  const updatedTicket = await response.json();
                  setTicket((prevTicket) => {
                    if (!prevTicket) return null;
                    return {
                      ...prevTicket,
                      ticket: { ...prevTicket.ticket, status: updatedTicket.ticket_status },
                    };
                  });
                  if (messageInput) {
                    messageInput.value = ""; // Clear the textarea
                  }
                } catch (error) {
                  console.error("Failed to resolve ticket:", error);
                }
              }}
            >
              Mark as Resolved
            </Button>}
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
      </div>
    </AdminDashboardLayout>
  );
}
