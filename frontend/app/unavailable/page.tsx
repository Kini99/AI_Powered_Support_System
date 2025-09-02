import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";
import { BookOpen } from "lucide-react";

// 1. Accept `searchParams` as a prop
export default function UnavailablePage({
  searchParams,
}: {
  searchParams: { label?: string };
}) {
  // 2. Get the label directly from the prop
  const label = searchParams.label || "This page";
  const displayLabel = label === "Dashboard" ? "Schedules" : label;

  return (
    <DashboardLayout>
      <div className="p-6">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">
          {displayLabel}
        </h1>
        <Card>
          <CardContent className="p-8 text-center">
            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No {displayLabel} Available
            </h3>
            <p className="text-gray-500">
              {displayLabel} will appear here when they are added.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}