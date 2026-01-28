"use client";
import React from "react";

const UseCases = () => {
  return (
    <section className="mx-auto w-[95%] md:w-7xl py-10 md:py-16">
      <div className="flex flex-col items-start gap-6">
        <h2 className="font-instrument font-medium text-3xl md:text-4xl text-tekk-darkest">
          Built for real workflows
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-darkest" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Product teams</h3>
            <p className="font-inter text-tekk-darkest/70">Market scans, competitor maps, and trend timelines.</p>
          </div>
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-primary" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Analysts</h3>
            <p className="font-inter text-tekk-darkest/70">Source heat-maps and evidence-backed briefs.</p>
          </div>
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-dark" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Researchers</h3>
            <p className="font-inter text-tekk-darkest/70">Literature reviews with transparent citations.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default UseCases;