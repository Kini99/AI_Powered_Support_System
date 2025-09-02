import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const ticketId = params.id
    
    // Mock ticket reopening
    console.log(`Reopening ticket ${ticketId}`)
    
    return NextResponse.json({
      message: 'Ticket reopened successfully'
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to reopen ticket' },
      { status: 500 }
    )
  }
}
