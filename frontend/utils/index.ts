export const getStatusColor = (status: string) => {
  switch (status) {
    case "Resolved":
      return "bg-green-100 text-green-800";
    case "Closed":
      return "bg-blue-100 text-blue-800";
    case "Open":
      return "bg-yellow-100 text-yellow-800";
    case "Work in Progress":
      return "bg-orange-100 text-orange-800";
    case "Student Action Required":
    case "Admin Action Required":
    case "Action Required":
      return "bg-red-100 text-red-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

export const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp.endsWith("Z") ? timestamp : timestamp + "Z");
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
