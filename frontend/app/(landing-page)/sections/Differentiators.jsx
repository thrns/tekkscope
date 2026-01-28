"use client";
import React from "react";

const Differentiators = () => {
  return (
    <section className="mx-auto w-[95%] md:w-7xl py-10 md:py-16">
      <div className="flex flex-col items-start gap-6">
        <h2 className="font-instrument font-medium text-3xl md:text-4xl text-tekk-darkest">
          Why choose Tekkscope
        </h2>
        <p className="font-inter text-tekk-darkest/80 text-base md:text-lg max-w-3xl">
          Built for product and research teams that need transparent, structured insights.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-darkest" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Insight clusters</h3>
            <p className="font-inter text-tekk-darkest/70">Group findings by theme for faster synthesis.</p>
          </div>
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-primary" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Contradiction alerts</h3>
            <p className="font-inter text-tekk-darkest/70">Surface conflicting claims with sources.</p>
          </div>
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-dark" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Export-ready reports</h3>
            <p className="font-inter text-tekk-darkest/70">PDF and CSV outputs designed for stakeholders.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Differentiators;