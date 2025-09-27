import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Get the request body
    const body = await request.json();

    // Make the POST request to the external API
    const response = await fetch(process.env.BOT_START_URL!, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // Check if the request was successful
    if (!response.ok) {
      throw new Error(`External API responded with status: ${response.status}`);
    }

    // Get the JSON response
    const data = await response.json();

    // Return the complete JSON response directly
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in offer API route:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
