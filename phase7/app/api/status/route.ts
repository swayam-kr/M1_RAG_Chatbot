import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
    try {
        const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000';
        const response = await fetch(`${backendUrl}/api/status`, { cache: 'no-store' });
        if (!response.ok) {
            return NextResponse.json({ status: 'offline', last_refreshed: 'Not yet run' }, { status: 200 });
        }
        const data = await response.json();
        return NextResponse.json(data);
    } catch {
        return NextResponse.json({ status: 'offline', last_refreshed: 'Not yet run' }, { status: 200 });
    }
}
