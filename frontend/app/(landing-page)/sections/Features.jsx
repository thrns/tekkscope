"use client";
import React from "react";

const Features = () => {
  return (
    <section className="mx-auto w-[95%] md:w-7xl py-10 md:py-16">
      <div className="flex flex-col items-start gap-6">
        <h2 className="font-instrument font-medium text-3xl md:text-4xl text-tekk-darkest">
          Research engine built for teams
        </h2>
        <p className="font-inter text-tekk-darkest/80 text-base md:text-lg max-w-3xl">
          Real-time insights with citations, structured deliverables, and an API-first workflow.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-2xl border border-tekk-dark bg-white p-6 flex flex-col gap-4">
            <div className="h-32 rounded-xl bg-tekk-darkest" />
            <h3 className="font-instrument font-medium text-xl text-tekk-darkest">Real-time answers</h3>
            <p className="font-inter text-tekk-darkest/70">Cited results and quick follow-ups to go deeper.</p>
          </div>
          <div className="rounded-2xl border border-tekk-dark bg-white p-6 flex flex-col gap-4">
            <div className="h-32 rounded-xl bg-tekk-primary" />
            <h3 className="font-instrument font-medium text-xl text-tekk-darkest">Structured deliverables</h3>
            <p className="font-inter text-tekk-darkest/70">Insight clusters, timelines, and export-ready summaries.</p>
          </div>
          <div className="rounded-2xl border border-tekk-dark bg-white p-6 flex flex-col gap-4">
            <div className="h-32 rounded-xl bg-tekk-dark" />
            <h3 className="font-instrument font-medium text-xl text-tekk-darkest">API-first</h3>
            <p className="font-inter text-tekk-darkest/70">SDKs and webhooks for automation and apps.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Features;