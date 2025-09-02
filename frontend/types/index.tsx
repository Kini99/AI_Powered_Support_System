export interface Message {
     id: string;
     ticket_id: string;
     sender_role: "student" | "admin" | "agent";
     sender_id?: string;
     message: string;
     confidence_score?: number;
     timestamp: string;
     sender_email?: string;
   }

export interface TicketDetail {
  id: string;
  user_id: string;
  category: string;
  status:
    | "Open"
    | "Work in Progress"
    | "Student Action Required"
    | "Admin Action Required"
    | "Resolved"
    | "Closed";
  title: string;
  message: string;
  subcategory_data?: any;
  from_date?: string;
  to_date?: string;
  attachments: string[];
  assigned_to?: string;
  rating?: number;
  created_at: string;
  updated_at?: string;
}

export const getMessageBackgroundColor = (role: string) => {
    switch (role) {
      case "student":
        return "bg-blue-50";
      case "admin":
        return "bg-green-50";
      case "agent":
        return "bg-yellow-50";
      default:
        return "bg-gray-50";
    }
  };

export interface Ticket {
  id: string;
  user_id: string;
  category: string;
  status:
    | "Open"
    | "Work in Progress"
    | "Student Action Required"
    | "Admin Action Required"
    | "Resolved"
    | "Closed";
  title: string;
  created_at: string;
  updated_at?: string;
  rating?: number;
  assigned_to?: string;
  assigned_admin_email?: string;
  response_count: number;
  last_response?: string;
  last_response_time?: string;
}