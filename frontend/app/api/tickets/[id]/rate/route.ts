import { NextRequest, NextResponse } from 'next/server'

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { rating } = await request.json()
    const ticketId = params.id
    
    // Mock rating update
    console.log(`Rating ticket ${ticketId} with ${rating} stars`)
    
    return NextResponse.json({
      message: 'Rating submitted successfully'
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to submit rating' },
      { status: 500 }
    )
  }
}
