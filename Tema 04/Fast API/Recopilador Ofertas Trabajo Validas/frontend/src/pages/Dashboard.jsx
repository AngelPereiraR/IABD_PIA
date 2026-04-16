import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchOffers, generateCV } from "../api/client";
import { StatusBadge } from "../components/StatusBadge";
import { ScoreBar } from "../components/ScoreBar";
import { FileText, ExternalLink } from "lucide-react";

export function Dashboard() {
  const qc = useQueryClient();
  const { data: offers = [], isLoading } = useQuery({
    queryKey: ["offers"],
    queryFn: () => fetchOffers({ limit: 50 }),
    refetchInterval: 30_000, // Poll cada 30s
  });

  const generate = useMutation({
    mutationFn: generateCV,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["offers"] }),
  });

  if (isLoading) return <p className="p-8 text-gray-500">Cargando ofertas...</p>;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">📋 Historial de Ofertas</h1>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3 text-left">Puesto</th>
              <th className="px-4 py-3 text-left">Empresa</th>
              <th className="px-4 py-3 text-left">Score</th>
              <th className="px-4 py-3 text-left">Estado</th>
              <th className="px-4 py-3 text-left">Fecha</th>
              <th className="px-4 py-3 text-left">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {offers.map((offer) => (
              <tr key={offer.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{offer.job_title ?? "—"}</td>
                <td className="px-4 py-3 text-gray-600">{offer.company ?? "—"}</td>
                <td className="px-4 py-3"><ScoreBar score={offer.score} /></td>
                <td className="px-4 py-3"><StatusBadge status={offer.status} /></td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(offer.created_at).toLocaleDateString("es-ES")}
                </td>
                <td className="px-4 py-3 flex gap-2">
                  {offer.optimized_cv_url ? (
                    <a
                      href={offer.optimized_cv_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-blue-600 hover:underline text-xs"
                    >
                      <FileText size={14} /> CV
                    </a>
                  ) : (
                    <button
                      onClick={() => generate.mutate(offer.id)}
                      disabled={offer.status === "processing" || generate.isPending}
                      className="text-xs bg-indigo-600 text-white px-2 py-1 rounded hover:bg-indigo-700 disabled:opacity-50"
                    >
                      {offer.status === "processing" ? "Generando..." : "Generar CV"}
                    </button>
                  )}
                  {offer.offer_url && (
                    <a href={offer.offer_url} target="_blank" rel="noopener noreferrer"
                       className="text-gray-400 hover:text-gray-600">
                      <ExternalLink size={14} />
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
