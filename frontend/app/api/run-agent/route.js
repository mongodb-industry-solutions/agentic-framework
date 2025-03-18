export async function GET(request) {
  const { searchParams } = new URL(request.url);
  const issue_report = searchParams.get("issue_report");
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    const apiEndpoint = `${apiUrl}/run-agent?issue_report=${encodeURIComponent(issue_report)}`;
    const res = await fetch(apiEndpoint);
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