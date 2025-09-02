'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/dashboard-layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Paperclip } from 'lucide-react'

const categories = [
  'Product Support',
  'Leave',
  'Attendance/Counselling Support',
  'Referral',
  'Evaluation Score',
  'Course Query',
  'Other Course Query',
  'Code Review',
  'Personal Query',
  'NBFC/ISA',
  'IA Support',
  'Missed Evaluation Submission',
  'Revision',
  'MAC',
  'Withdrawal',
  'Late Evaluation Submission',
  'Feedback',
  'Placement Support - Placements',
  'Offer Stage- Placements',
  'ISA/EMI/NBFC/Glide Related - Placements',
  'Session Support - Placement'
]

const productTypes = [
  'Course Platform',
  'OJ',
  'Zoom',
  'Slack',
  'HUKUMU Interview',
  'Concept Explainer (CE)'
]

const issueTypes = [
  'Access required / Unable to login',
  'Query on how to use the product',
  'Interview',
  'Links',
  'Technical Issues'
]

export default function CreateTicketPage() {
  const [category, setCategory] = useState('')
  const [title, setTitle] = useState('')
  const [message, setMessage] = useState('')
  const [productType, setProductType] = useState('')
  const [issueType, setIssueType] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Real API call - post to backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/v1/tickets/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          category,
          title,
          message,
          subcategory_data: {
            product_type: productType,
            issue_type: issueType
          }
        })
      })

      if (response.ok) {
        router.push('/support')
      }
    } catch (error) {
      console.error('Failed to create ticket:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const showProductFields = category === 'Product Support'

  return (
    <DashboardLayout>
      <div className="p-6 max-w-4xl">
        <h1 className="text-2xl font-semibold text-gray-900 mb-6">Create Support Ticket</h1>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Category Selection */}
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select value={category} onValueChange={setCategory} required>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Product Support Specific Fields */}
          {showProductFields && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Label className="text-sm font-medium text-gray-700">PRODUCT</Label>
                <RadioGroup value={productType} onValueChange={setProductType}>
                  {productTypes.map((type) => (
                    <div key={type} className="flex items-center space-x-2">
                      <RadioGroupItem value={type} id={type} />
                      <Label htmlFor={type} className="text-sm">
                        {type}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>

              <div className="space-y-4">
                <Label className="text-sm font-medium text-gray-700">ISSUE-TYPE</Label>
                <RadioGroup value={issueType} onValueChange={setIssueType}>
                  {issueTypes.map((type) => (
                    <div key={type} className="flex items-center space-x-2">
                      <RadioGroupItem value={type} id={type} />
                      <Label htmlFor={type} className="text-sm">
                        {type}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            </div>
          )}

          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              placeholder="Enter the title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          {/* Message */}
          <div className="space-y-2">
            <Label htmlFor="message">Message</Label>
            <div className="border rounded-lg">
              {/* Rich Text Editor Toolbar */}
              <div className="flex items-center space-x-2 p-2 border-b bg-gray-50">
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => {
                  // Bold: Markdown style
                  const textarea = document.getElementById('message') as HTMLTextAreaElement;
                  if (!textarea) return;
                  const start = textarea.selectionStart;
                  const end = textarea.selectionEnd;
                  const before = message.slice(0, start);
                  const selected = message.slice(start, end);
                  const after = message.slice(end);
                  const newText = before + '**' + selected + '**' + after;
                  setMessage(newText);
                  setTimeout(() => {textarea.focus(); textarea.setSelectionRange(start+2, end+2);}, 0);
                }}>
                  <strong>B</strong>
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => {
                  // Italic: Markdown style
                  const textarea = document.getElementById('message') as HTMLTextAreaElement;
                  if (!textarea) return;
                  const start = textarea.selectionStart;
                  const end = textarea.selectionEnd;
                  const before = message.slice(0, start);
                  const selected = message.slice(start, end);
                  const after = message.slice(end);
                  const newText = before + '*' + selected + '*' + after;
                  setMessage(newText);
                  setTimeout(() => {textarea.focus(); textarea.setSelectionRange(start+1, end+1);}, 0);
                }}>
                  <em>I</em>
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0" onClick={() => {
                  // Underline: HTML tag
                  const textarea = document.getElementById('message') as HTMLTextAreaElement;
                  if (!textarea) return;
                  const start = textarea.selectionStart;
                  const end = textarea.selectionEnd;
                  const before = message.slice(0, start);
                  const selected = message.slice(start, end);
                  const after = message.slice(end);
                  const newText = before + '<u>' + selected + '</u>' + after;
                  setMessage(newText);
                  setTimeout(() => {textarea.focus(); textarea.setSelectionRange(start+3, end+3);}, 0);
                }}>
                  <u>U</u>
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  🔗
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  ≡
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  ⋯
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  {'{}'}
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  ⚡
                </Button>
                <div className="flex-1"></div>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  ↩
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  ↪
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  ⊞
                </Button>
                <Button type="button" variant="ghost" size="sm" className="h-8 w-8 p-0">
                  ✕
                </Button>
              </div>
              
              <Textarea
                id="message"
                placeholder="Type your message..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
                className="min-h-[200px] border-0 resize-none focus:ring-0"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between">
            <Button type="button" variant="ghost" size="sm">
              <Paperclip className="h-4 w-4 mr-2" />
              Attach files
            </Button>
            
            <Button 
              type="submit" 
              className="bg-blue-600 hover:bg-blue-700"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Creating...' : 'CREATE TICKET'}
            </Button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}
