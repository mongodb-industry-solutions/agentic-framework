// app/api/resume-agent/route.js
export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const thread_id = searchParams.get("thread_id");
  if (!thread_id) {
    return new Response(JSON.stringify({ error: "thread_id is required" }), { status: 400 });
  }
  try {
    const res = await fetch(`http://localhost:8000/api/resume-agent?thread_id=${encodeURIComponent(thread_id)}`);
    const data = await res.json();
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
