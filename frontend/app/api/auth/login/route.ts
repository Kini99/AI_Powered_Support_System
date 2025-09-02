import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()
    
    // Mock authentication logic
    // In a real app, you would validate against a database
    const mockUsers = [
      { email: 'student@masai.com', password: 'password', role: 'student' },
      { email: 'admin@masai.com', password: 'password', role: 'admin' },
      { email: 'kinjal@masai.com', password: 'password', role: 'student' },
    ]
    
    const user = mockUsers.find(u => u.email === email && u.password === password)
    
    if (!user) {
      return NextResponse.json(
        { error: 'Invalid credentials' },
        { status: 401 }
      )
    }
    
    return NextResponse.json({
      message: 'Login successful',
      role: user.role,
      email: user.email
    })
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
