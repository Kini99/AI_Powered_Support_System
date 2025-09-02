"use client";

import AdminDashboardLayout from "@/components/admin-dashboard-layout";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Ticket } from "@/types";
import { formatTimestamp, getStatusColor } from "@/utils";
import { MessageSquare, Star } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AdminSupportPage() {
  const [activeTab, setActiveTab] = useState<"unresolved" | "resolved">(
    "unresolved"
  );
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [userRole, setUserRole] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const role = localStorage.getItem("userRole");
    setUserRole(role);

    const fetchTickets = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE}/v1/tickets/my_tickets`,
          {
            credentials: "include",
          }
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: Ticket[] = await response.json();
        setTickets(data);
      } catch (error) {
        console.error("Failed to fetch tickets:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTickets();
  }, []);

  const filteredTickets = tickets.filter((ticket) => {
    if (activeTab === "resolved") {
      return ticket.status === "Resolved" || ticket.status === "Closed";
    }
    return ticket.status !== "Resolved" && ticket.status !== "Closed";
  });

  const renderStars = (rating?: number) => {
    if (!rating) return <span className="text-gray-400">--</span>;

    return (
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`h-4 w-4 ${
              star <= rating ? "text-yellow-400 fill-current" : "text-gray-300"
            }`}
          />
        ))}
      </div>
    );
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

  return (
    <AdminDashboardLayout>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">
            Support Tickets
          </h1>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-6">
          <button
            onClick={() => setActiveTab("unresolved")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "unresolved"
                ? "bg-gray-200 text-gray-900"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Unresolved
          </button>
          <button
            onClick={() => setActiveTab("resolved")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === "resolved"
                ? "bg-blue-100 text-blue-700"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Resolved
          </button>
        </div>

        {/* Tickets List */}
        <div className="space-y-4">
          {filteredTickets.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  No {activeTab} tickets
                </h3>
                <p className="text-gray-500">
                  {activeTab === "resolved"
                    ? "You don't have any resolved tickets yet."
                    : "You don't have any unresolved tickets."}
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredTickets.map((ticket) => (
              <Card
                key={ticket.id}
                className="hover:shadow-md transition-shadow"
              >
                <Link
                  href={`/adminSupport/ticket/${ticket.id}`}
                  className="text-lg font-medium text-gray-900 hover:text-blue-600 transition-colors"
                >
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        {ticket.title}

                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                          <div className="flex items-center space-x-1">
                            <MessageSquare className="h-4 w-4" />
                            <span>
                              {ticket.response_count - 1} Response
                              {ticket.response_count - 1 > 0 ? "s" : ""}
                            </span>
                          </div>
                          <span>•</span>
                          <span>{ticket.assigned_to || "Unassigned"}</span>
                          <span>•</span>
                          <span>
                            Last Updated on{" "}
                            {formatTimestamp(
                              ticket.updated_at || ticket.created_at
                            )}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-4">
                        {ticket.rating && (
                          <div className="flex items-center space-x-2">
                            <span className="text-sm text-gray-500">
                              You rated
                            </span>
                            {renderStars(ticket.rating)}
                          </div>
                        )}
                        <Badge className={getStatusColor(ticket.status)}>
                          {ticket.status === "Student Action Required"
                            ? "WORK IN PROGRESS"
                            : ticket.status.toUpperCase()}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Link>
              </Card>
            ))
          )}
        </div>
      </div>
    </AdminDashboardLayout>
  );
}
