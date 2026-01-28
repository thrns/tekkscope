import React from "react";

const Security = () => {
  return (
    <section className="mx-auto w-[95%] md:w-7xl py-10 md:py-16">
      <div className="flex flex-col items-start gap-6">
        <h2 className="font-instrument font-medium text-3xl md:text-4xl text-tekk-darkest">
          Enterprise-ready controls
        </h2>
        <p className="font-inter text-tekk-darkest/80 text-base md:text-lg max-w-3xl">
          Keep data private with configurable retention, access controls, and visibility features.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-20 rounded-lg bg-tekk-darkest" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Data privacy</h3>
            <p className="font-inter text-tekk-darkest/70">Private searches and configurable deletion windows.</p>
          </div>
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-20 rounded-lg bg-tekk-primary" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">User management</h3>
            <p className="font-inter text-tekk-darkest/70">Manage who can upload, download, and share answers.</p>
          </div>
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-20 rounded-lg bg-tekk-dark" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">SSO</h3>
            <p className="font-inter text-tekk-darkest/70">Single sign-on and centralized access policies.</p>
          </div>
          <div className="rounded-2xl bg-white border border-tekk-dark p-6 flex flex-col gap-3">
            <div className="h-20 rounded-lg bg-tekk-darkest" />
            <h3 className="font-instrument font-medium text-lg text-tekk-darkest">Audit visibility</h3>
            <p className="font-inter text-tekk-darkest/70">Track activity with audit logs for compliance.</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Security;