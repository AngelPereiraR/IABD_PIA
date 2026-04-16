const STATUS_STYLES = {
  pending:    "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  done:       "bg-green-100 text-green-800",
  error:      "bg-red-100 text-red-800",
};

export function StatusBadge({ status }) {
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_STYLES[status] ?? "bg-gray-100"}`}>
      {status}
    </span>
  );
}
