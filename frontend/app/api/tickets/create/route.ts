import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { category, title, message, subcategory_data } = body
    
    // Mock ticket creation
    const ticketId = `TKT-${Math.random().toString(36).substr(2, 9).toUpperCase()}`
    
    // In a real app, you would save to database
    console.log('Creating ticket:', {
      id: ticketId,
      category,
      title,
      message,
      subcategory_data,
      status: 'Open',
      created_at: new Date().toISOString()
    })
    
    return NextResponse.json({
      message: 'Ticket created successfully',
      ticket_id: ticketId
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create ticket' },
      { status: 500 }
    )
  }
}
