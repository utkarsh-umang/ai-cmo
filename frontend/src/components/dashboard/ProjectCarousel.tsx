import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ProjectCard } from "./ProjectCard";
import type { Project } from "../../types";

interface ProjectCarouselProps {
  projects: Project[];
}

export function ProjectCarousel({ projects }: ProjectCarouselProps) {
  const [index, setIndex] = useState(0);
  const [itemsPerPage, setItemsPerPage] = useState(4);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const updateItemsPerPage = () => {
      const width = window.innerWidth;
      if (width < 768) {
        setItemsPerPage(1);
      } else if (width < 1024) {
        setItemsPerPage(2);
      } else if (width < 1280) {
        setItemsPerPage(3);
      } else {
        setItemsPerPage(4);
      }
    };

    updateItemsPerPage();
    window.addEventListener("resize", updateItemsPerPage);
    return () => window.removeEventListener("resize", updateItemsPerPage);
  }, []);

  const maxIndex = Math.max(0, projects.length - itemsPerPage);

  const next = () => {
    setIndex((prev) => (prev >= maxIndex ? 0 : prev + 1));
  };

  const prev = () => {
    setIndex((prev) => (prev <= 0 ? maxIndex : prev - 1));
  };

  return (
    <div className="relative group -mx-4 px-4 pb-4">
      <div className="flex items-center justify-between mb-6 px-2">
        <div>
          <h2 className="text-sm font-black uppercase tracking-[0.2em] text-accent-dark/40">
            Active Projects
          </h2>
          <p className="text-xs font-bold text-accent-dark/20 mt-1">
            {projects.length} Total • Showing {index + 1}-{Math.min(index + itemsPerPage, projects.length)}
          </p>
        </div>
        <div className="flex gap-2.5">
          <button
            onClick={prev}
            className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white border border-brand-100/50 text-brand-500 shadow-sm transition-all hover:bg-brand-500 hover:text-white hover:shadow-lg hover:shadow-brand-500/20 active:scale-95 disabled:opacity-30"
            disabled={projects.length <= itemsPerPage}
          >
            <ChevronLeft size={22} strokeWidth={2.5} />
          </button>
          <button
            onClick={next}
            className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white border border-brand-100/50 text-brand-500 shadow-sm transition-all hover:bg-brand-500 hover:text-white hover:shadow-lg hover:shadow-brand-500/20 active:scale-95 disabled:opacity-30"
            disabled={projects.length <= itemsPerPage}
          >
            <ChevronRight size={22} strokeWidth={2.5} />
          </button>
        </div>
      </div>

      <div className="relative overflow-hidden" ref={containerRef}>
        <motion.div
          className="flex gap-6 py-2"
          animate={{
            x: `calc(-${index * (100 / itemsPerPage)}% - ${index * (24 / itemsPerPage)}px)`,
          }}
          transition={{
            type: "spring",
            stiffness: 260,
            damping: 28,
            mass: 1
          }}
        >
          {projects.map((project, i) => (
            <motion.div
              key={project.id}
              className="shrink-0"
              style={{
                width: `calc(${100 / itemsPerPage}% - ${((itemsPerPage - 1) * 24) / itemsPerPage}px)`,
              }}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.05 }}
            >
              <ProjectCard project={project} />
            </motion.div>
          ))}
        </motion.div>
      </div>

      {/* Scroll indicator dots */}
      {projects.length > itemsPerPage && (
        <div className="mt-8 flex justify-center gap-1.5">
          {Array.from({ length: maxIndex + 1 }).map((_, i) => (
            <button
              key={i}
              onClick={() => setIndex(i)}
              className={`h-1.5 rounded-full transition-all duration-300 ${i === index ? "w-8 bg-brand-500" : "w-1.5 bg-brand-200 hover:bg-brand-300"
                }`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
