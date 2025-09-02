"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useEffect, useState } from "react";
import {
  BookOpen,
  TrendingUp,
  Users,
  CheckCircle,
  AlertTriangle,
  HelpCircle,
} from "lucide-react";
import AdminDashboardLayout from "@/components/admin-dashboard-layout";

interface AnalyticsSummary {
  total_agent_resolved: number;
  total_human_resolved: number;
  total_escalated: number;
  agent_success_rate: number;
  average_confidence_score: number;
  cache_hits: number;
}

interface RagasEvaluation {
  faithfulness: number;
  answer_relevancy: number;
  context_precision: number;
  context_recall: number;
  last_updated: string;
}

interface AnalyticsData {
  summary: AnalyticsSummary;
  ragas_evaluation: RagasEvaluation;
}

export default function AdminDashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAnalytics() {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/v1/admin/analytics?category=EC`, {
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error("Failed to fetch analytics");
        }
        const data = await response.json();
        setAnalytics(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <AdminDashboardLayout>
        <div className="p-6">
          <h1 className="text-2xl font-semibold text-gray-900 mb-6">
            Admin Dashboard
          </h1>
          <p>Loading analytics...</p>
        </div>
      </AdminDashboardLayout>
    );
  }

  if (!analytics) {
    return (
      <AdminDashboardLayout>
        <div className="p-6">
          <h1 className="text-2xl font-semibold text-gray-900 mb-6">
            Admin Dashboard
          </h1>
          <Card>
            <CardContent className="p-8 text-center">
              <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Could not load analytics
              </h3>
              <p className="text-gray-500">
                There was an error fetching the dashboard data. Please try again
                later.
              </p>
            </CardContent>
          </Card>
        </div>
      </AdminDashboardLayout>
    );
  }

  const { summary, ragas_evaluation } = analytics;

  return (
    <AdminDashboardLayout>
      <div className="p-6 bg-gray-50 min-h-screen">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          Admin Dashboard
        </h1>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Agent Success Rate
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {summary.agent_success_rate}%
              </div>
              <p className="text-xs text-muted-foreground">
                Automated resolutions vs. escalations
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Avg. Confidence
              </CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {summary.average_confidence_score}%
              </div>
              <p className="text-xs text-muted-foreground">
                Agent's confidence in its answers
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">
                Total Escalations
              </CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {summary.total_escalated}
              </div>
              <p className="text-xs text-muted-foreground">
                Tickets passed to human agents
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium">Cache Hits</CardTitle>
              <HelpCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.cache_hits}</div>
              <p className="text-xs text-muted-foreground">
                Queries resolved from cache
              </p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Resolutions Breakdown */}
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Resolution Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Resolved by Agent</span>
                  <span className="text-lg font-bold">
                    {summary.total_agent_resolved}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full"
                    style={{
                      width: `${
                        (summary.total_agent_resolved /
                          (summary.total_agent_resolved +
                            summary.total_human_resolved)) *
                        100
                      }%`,
                    }}
                  ></div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Resolved by Human</span>
                  <span className="text-lg font-bold">
                    {summary.total_human_resolved}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div
                    className="bg-green-500 h-2.5 rounded-full"
                    style={{
                      width: `${
                        (summary.total_human_resolved /
                          (summary.total_agent_resolved +
                            summary.total_human_resolved)) *
                        100
                      }%`,
                    }}
                  ></div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* RAGAS Evaluation */}
          {/* <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>RAGAS Model Evaluation</CardTitle>
              <p className="text-sm text-gray-500">
                Offline evaluation of response quality. Last updated:{" "}
                {new Date(ragas_evaluation.last_updated).toLocaleDateString()}
              </p>
            </CardHeader>
            <CardContent className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold">
                  {ragas_evaluation.faithfulness}
                </p>
                <p className="text-sm text-muted-foreground">Faithfulness</p>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {ragas_evaluation.answer_relevancy}
                </p>
                <p className="text-sm text-muted-foreground">
                  Answer Relevancy
                </p>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {ragas_evaluation.context_precision}
                </p>
                <p className="text-sm text-muted-foreground">
                  Context Precision
                </p>
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {ragas_evaluation.context_recall}
                </p>
                <p className="text-sm text-muted-foreground">Context Recall</p>
              </div>
            </CardContent>
          </Card> */}
        </div>
      </div>
    </AdminDashboardLayout>
  );
}
