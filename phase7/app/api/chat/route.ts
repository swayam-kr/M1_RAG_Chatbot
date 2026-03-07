import { NextResponse } from 'next/server';

export async function POST(req: Request) {
    try {
        const body = await req.json();

        const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
        // Proxy request strictly to our Phase 5/6 internal FastAPI Microservice Gateway
        const response = await fetch(`${backendUrl}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            return NextResponse.json({ error: "Upstream Backend Error" }, { status: response.status });
        }

        const data = await response.json();
        return NextResponse.json(data);

    } catch (error) {
        console.error("Next.js Proxy Error:", error);
        return NextResponse.json(
            { error: "Failed to connect to Python backend." },
            { status: 500 }
        );
    }
}
