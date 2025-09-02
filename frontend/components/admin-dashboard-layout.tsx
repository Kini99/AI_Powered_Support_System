"use client";

import { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  LayoutDashboard,
  Bell,
  BookOpen,
  Users,
  MessageSquare,
  HelpCircle,
  Search,
  Settings,
  LogOut,
  ChevronLeft,
  MoreHorizontal,
  Bookmark,
  FileText,
} from "lucide-react";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function AdminDashboardLayout({ children }: DashboardLayoutProps) {
  // const [userRole, setUserRole] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  // const [notifications, setNotifications] = useState(3);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // const role = localStorage.getItem("userRole");
    const email = localStorage.getItem("userEmail");
    // setUserRole(role);
    setUserEmail(email);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("authToken");
    localStorage.removeItem("userRole");
    localStorage.removeItem("userEmail");
    router.push("/");
  };

  const navigationItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/admin" },
    { icon: FileText, label: "Support Documents", href:"/admin/documents" },
    { icon: MessageSquare, label: "Support Ticket", href: "/adminSupport" },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex flex-1 flex-row">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900">masai</h1>
        </div>

        <nav className="px-4 space-y-1">
          {navigationItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-50 text-blue-700 border-r-2 border-blue-700"
                    : "text-gray-700 hover:bg-gray-50"
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}

          <div className="pt-4">
            <Button
              variant="ghost"
              className="w-full justify-start text-gray-700"
            >
              <MoreHorizontal className="mr-3 h-5 w-5" />
              More
            </Button>
          </div>
        </nav>
      </aside>
      
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <ChevronLeft className="h-5 w-5 text-gray-400" onClick={()=> router.back()} />
              <div className="flex items-center space-x-4">
                <Search className="h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search by concepts, lectures, assignment etc..."
                  className="bg-transparent text-sm text-gray-600 placeholder-gray-400 border-none outline-none w-96"
                />
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-5 w-5" />
                {/* {notifications > 0 && (
                  <Badge className="absolute -top-1 -right-1 h-5 w-5 rounded-full bg-red-500 text-xs flex items-center justify-center">
                    {notifications}
                  </Badge>
                )} */}
              </Button>

              <Button variant="ghost" size="sm">
                <Settings className="h-5 w-5" />
              </Button>

              <Button variant="ghost" size="sm">
                <Bookmark className="h-5 w-5" />
              </Button>

              <Button variant="ghost" size="sm">
                <FileText className="h-5 w-5" />
              </Button>

               <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="ghost"
                      className="relative h-8 w-8 rounded-full"
                    >
                      <Avatar className="h-8 w-8">
                        <AvatarImage
                          src="https://thumbs.dreamstime.com/b/user-profile-vector-flat-illustration-avatar-person-icon-gender-neutral-silhouette-profile-picture-user-profile-vector-flat-304778094.jpg"
                          alt="User"
                        />
                        <AvatarFallback>
                          {userEmail ? userEmail.charAt(0).toUpperCase() : "U"}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                    {userEmail && (
                      <span className="text-sm font-medium text-gray-700">
                        {userEmail.split("@")[0]}
                      </span>
                    )}
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        <div className="flex">
          {/* Main Content */}
          <main className="flex-1">{children}</main>
        </div>
      </div>
    </div>
  );
}
