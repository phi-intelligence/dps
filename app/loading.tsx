export default function Loading() {
  return (
    <div className="flex min-h-[50vh] w-full items-center justify-center" aria-label="Loading">
      <div className="flex flex-col items-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-[#e2c977]/30 border-t-[#e2c977]" />
        <span className="text-[10px] font-technical font-bold uppercase tracking-[0.3em] text-[#b3c0d0]">
          Loading
        </span>
      </div>
    </div>
  );
}
