"use client";
import React from "react";

const Integrations = () => {
  return (
    <section className="mx-auto w-[95%] md:w-7xl py-10 md:py-16">
      <div className="flex flex-col items-start gap-6">
        <h2 className="font-instrument font-medium text-3xl md:text-4xl text-tekk-darkest">
          Integrations and API
        </h2>
        <p className="font-inter text-tekk-darkest/80 text-base md:text-lg max-w-3xl">
          Build automation with SDKs, webhooks, and simple endpoints.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-2xl border border-tekk-dark bg-white p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-primary" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">SDKs</h3>
            <p className="font-inter text-tekk-darkest/70">Client libraries for rapid integration.</p>
          </div>
          <div className="rounded-2xl border border-tekk-dark bg-white p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-darkest" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Webhooks</h3>
            <p className="font-inter text-tekk-darkest/70">Trigger workflows and receive updates.</p>
          </div>
          <div className="rounded-2xl border border-tekk-dark bg-white p-6 flex flex-col gap-3">
            <div className="h-24 rounded-lg bg-tekk-dark" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Exports</h3>
            <p className="font-inter text-tekk-darkest/70">Push to dashboards and BI tools.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Integrations;