import React from 'react';
import { Container } from '@/components/ui/container';
import Footer from '../sections/Footer';
function TermsOfService() {
  return (
    <>
      <Container className="w-full py-40">
        <div className="mx-auto h-full max-w-3xl overflow-y-auto rounded-lg border p-4 text-left leading-relaxed">
          <section className="mx-auto max-w-3xl text-center">
            <h1 className="mb-4 text-3xl font-bold">Terms of Service</h1>
            <p className="mb-4">Last updated: January 2025</p>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">1. Introduction</h2>
            <p>
              Welcome to Tekkscope! These Terms and Conditions govern your use
              of our AI-powered research services, API, and website. By accessing
              or using our services, you agree to be bound by these Terms. If you
              disagree with any part of the terms, you may not access the service.
            </p>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">2. Intellectual Property</h2>
            <p>
              The content, layout, design, data, databases, graphics, and AI
              research algorithms on this website and service are protected by
              intellectual property laws and are owned by or licensed to Tekkscope.
              Research reports generated through our service are provided for your
              use, but our underlying technology, algorithms, and service structure
              remain our intellectual property. Unless otherwise stated, you may not
              reproduce, distribute, modify, transmit, reuse, download, repost,
              copy, or use any of the content on this website for commercial
              purposes without express written permission from us.
            </p>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">3. User Responsibilities</h2>
            <p>
              As a user, you agree to use the website and research services only
              for lawful purposes and in a way that does not infringe the rights
              of, restrict, or inhibit anyone else's use and enjoyment of the
              service. You agree not to:
            </p>
            <ul className="list-disc pl-5 mt-2">
              <li>Use the service for any illegal or unauthorized purpose.</li>
              <li>Attempt to reverse engineer or extract our AI models or algorithms.</li>
              <li>Submit queries that violate intellectual property rights or contain malicious content.</li>
              <li>Exceed reasonable usage limits or attempt to abuse the API.</li>
              <li>Share or resell API access without authorization.</li>
            </ul>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">4. Limitations of Liability</h2>
            <p>
              To the fullest extent permitted by law, Tekkscope shall not be
              liable for any indirect, incidental, special, consequential, or
              punitive damages, or any loss of profits or revenues, whether
              incurred directly or indirectly, or any loss of data, use,
              goodwill, or other intangible losses, resulting from your access
              to or use of, or inability to access or use, the website or
              services. Research reports are generated using AI technology and
              may contain inaccuracies. You acknowledge that research results
              should be verified and that Tekkscope does not guarantee the
              accuracy, completeness, or reliability of generated research content.
            </p>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">5. Service Availability and Credits</h2>
            <p>
              Tekkscope services are provided on a credit-based system. Credits
              are consumed based on API usage and research query complexity. Unused
              credits may expire according to your subscription terms. We reserve
              the right to modify service availability, pricing, and credit
              consumption rates with reasonable notice.
            </p>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">6. Governing Law</h2>
            <p>
              These Terms shall be governed and construed in accordance with the
              laws of the jurisdiction in which Tekkscope operates, without regard
              to its conflict of law provisions.
            </p>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">7. Changes to Terms</h2>
            <p className="font-medium">
              We reserve the right to modify or replace these Terms at any time.
              The most current version will be posted on our website. By
              continuing to access or use our services after those revisions
              become effective, you agree to be bound by the revised terms.
            </p>
          </section>

          <section>
            <h2 className="mt-4 font-semibold">8. Termination</h2>
            <p>
              We may terminate or suspend your access to our services
              immediately, without prior notice or liability, for any reason
              whatsoever, including without limitation if you breach the Terms.
              Upon termination, your right to use the service will cease
              immediately, and any unused credits may be forfeited according to
              our refund policy.
            </p>
          </section>

          <section className="mx-auto mt-4 max-w-3xl text-left leading-relaxed">
            <h2 className="mt-4 font-semibold">9. Contact Us</h2>
            <p>
              If you have any questions about these Terms, please contact us at:
            </p>
            <p className="font-bold">Tekkscope</p>
            <p>
              <a
                href="mailto:support@tekkscope.com"
                className="text-blue-600 underline"
              >
                support@tekkscope.com
              </a>
            </p>
          </section>
        </div>
      </Container>
      <Footer />
    </>
  );
}

export default TermsOfService;
