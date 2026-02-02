import React from 'react';
import Footer from '../sections/Footer';
import { Container } from '@/components/ui/container';

function PrivacyPolicy() {
  return (
    <>
      <Container className="w-full py-40">
        <div className="mx-auto h-full max-w-3xl overflow-y-auto rounded-lg border p-4 text-left leading-relaxed">
          <section className="mx-auto max-w-3xl text-center">
            <h1 className="mb-4 text-3xl font-bold">Privacy Policy</h1>
            <p className="mb-4">Last updated: January 2025</p>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">1. Introduction</h2>
            <p>
              Welcome to Tekkscope. We respect your privacy and are committed
              to protecting your personal data. This Privacy Policy will inform
              you about how we look after your personal data when you use our
              AI-powered research services and tell you about your privacy rights
              and how the law protects you.
            </p>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">2. Data We Collect</h2>
            <p>
              We may collect, use, store, and transfer different kinds of
              personal data about you, which we have grouped together as
              follows:
            </p>
            <ul className="list-disc pl-5">
              <li>
                <strong>Identity Data:</strong> Name, username, or similar
                identifier.
              </li>
              <li>
                <strong>Contact Data:</strong> Email address, telephone numbers,
                and mailing address.
              </li>
              <li>
                <strong>Technical Data:</strong> IP address, browser type and
                version, time zone setting, browser plug-in types and versions,
                operating system, and platform.
              </li>
              <li>
                <strong>Usage Data:</strong> Information about how you use our
                website, API services, and research features, including queries
                submitted and reports generated.
              </li>
              <li>
                <strong>API Usage Data:</strong> Research queries, generated
                reports, and API usage patterns for service improvement and
                analytics.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">3. How We Use Your Data</h2>
            <p>
              We will only use your personal data when the law allows us to.
              Most commonly, we will use your personal data in the following
              circumstances:
            </p>
            <ul className="list-disc pl-5">
              <li>To provide you with our AI-powered research services and API access.</li>
              <li>To process your research queries and generate reports.</li>
              <li>To manage our relationship with you and provide customer support.</li>
              <li>To improve our research algorithms and service quality.</li>
              <li>To comply with legal obligations.</li>
            </ul>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">4. Data Sharing</h2>
            <p>
              We may share your personal data with third parties in the
              following circumstances:
            </p>
            <ul className="list-disc pl-5">
              <li>With AI service providers (such as Google Gemini) who power our research capabilities.</li>
              <li>With service providers who help us provide our services (hosting, payment processing, analytics).</li>
              <li>
                For legal reasons, such as to comply with a legal obligation or
                protect our rights.
              </li>
              <li>With your consent or at your direction.</li>
            </ul>
            <p className="mt-2">
              <strong>Note:</strong> Research queries and generated content may be processed by third-party AI services to provide our research functionality. We do not share your personal information for training AI models or other purposes beyond service delivery.
            </p>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">5. Your Rights</h2>
            <p>
              Under certain circumstances, you have rights under data protection
              laws in relation to your personal data. These include the right
              to:
            </p>
            <ul className="list-disc pl-5">
              <li>Request access to your personal data.</li>
              <li>Request correction of your personal data.</li>
              <li>Request erasure of your personal data.</li>
              <li>Object to processing of your personal data.</li>
              <li>Request restriction of processing your personal data.</li>
              <li>Request transfer of your personal data.</li>
              <li>Withdraw consent at any time.</li>
            </ul>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">6. Data Security</h2>
            <p>
              We have put in place appropriate security measures to prevent your
              personal data from being accidentally lost, used, or accessed in
              an unauthorized way, altered, or disclosed.
            </p>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">
              7. Changes to This Privacy Policy
            </h2>
            <p>
              We keep our Privacy Policy under regular review. This Privacy
              Policy was last updated in January 2025. It may change in the
              future, and any changes will be posted on this page.
            </p>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">8. Contact Us</h2>
            <p>
              If you have any questions about this Privacy Policy or our data
              practices, please contact us at:
            </p>
            <p className="mt-2 text-xl font-bold">Tekkscope</p>
            <p>
              <a
                href="mailto:support@tekkscope.com"
                className="text-blue-600 underline"
              >
                support@tekkscope.com
              </a>
            </p>
          </section>

          <section>
            <h2 className="mb-2 mt-4 font-semibold">
              9. AI Service Providers
            </h2>
            <p>
              Tekkscope uses third-party AI services (such as Google Gemini) to
              power our research capabilities. Research queries are sent to these
              services to generate research reports. We do not use your data to
              train or improve generalized AI models beyond providing the research
              services you request. All AI service providers are bound by their
              respective privacy policies and data protection agreements.
            </p>
          </section>
        </div>
      </Container>
      <Footer />
    </>
  );
}

export default PrivacyPolicy;
