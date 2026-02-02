'use client';

import React from 'react';
import { Container } from '@/components/ui/container';
import Footer from '../sections/Footer';

const RefundPolicyPage = () => {
  return (
    <>
      <Container className="w-full py-40">
        <h1 className="mb-6 text-3xl font-bold">
          Refund & Cancellation Policy
        </h1>

        <div className="prose dark:prose-invert">
          <p className="mb-4">Last Updated: January 2025</p>

          <h2 className="mb-3 mt-6 text-xl font-semibold">Overview</h2>
          <p>
            Tekkscope is committed to providing high-quality AI-powered research
            services. This Refund and Cancellation Policy outlines the terms and
            conditions regarding subscription cancellations and refund requests
            for our research API services.
          </p>

          <h2 className="mb-3 mt-6 text-xl font-semibold">
            Subscription Cancellation
          </h2>
          <p>
            Customers can cancel their subscription at any time by logging into
            their account and navigating to the subscription settings page. Upon
            cancellation:
          </p>
          <ul className="my-3 list-disc pl-6">
            <li>
              Access to premium features will continue until the end of the
              current billing cycle.
            </li>
            <li>No further charges will be made after cancellation.</li>
            <li>
              We do not provide partial refunds for unused portions of
              subscription periods.
            </li>
            <li>
              Data associated with your account may be retained for a limited
              period as outlined in our Privacy Policy.
            </li>
          </ul>

          <h2 className="mb-3 mt-6 text-xl font-semibold">Refund Policy</h2>
          <p>
            Due to the digital nature of our services, all purchases are
            generally final and non-refundable once the service has been
            activated. However, refunds may be considered in the following
            exceptional circumstances:
          </p>
          <ul className="my-3 list-disc pl-6">
            <li>
              <strong>Accidental Purchases:</strong> If you've been charged
              multiple times for the same subscription due to a technical error,
              we will refund the duplicate charges.
            </li>
            <li>
              <strong>Service Unavailability:</strong> If our service
              experiences significant technical issues that render it completely
              unusable for a continuous period of more than 72 hours, affected
              customers may be eligible for a partial refund proportional to the
              service outage.
            </li>
            <li>
              <strong>Unauthorized Charges:</strong> If you discover
              unauthorized charges from Tekkscope on your account, please
              contact your payment provider immediately and then notify our
              support team.
            </li>
          </ul>

          <p className="mt-4">
            Please note that the following are explicitly excluded from our
            refund policy:
          </p>
          <ul className="my-3 list-disc pl-6">
            <li>Requests for refunds based on lack of usage.</li>
            <li>
              Requests for refunds after account cancellation if the
              subscription was actively used.
            </li>
            <li>
              Requests for refunds after the subscription has auto-renewed if
              the cancellation option was available.
            </li>
            <li>
              Dissatisfaction with the service features that were clearly
              described at the time of purchase.
            </li>
          </ul>

          <h2 className="mb-3 mt-6 text-xl font-semibold">
            How to Request a Refund
          </h2>
          <p>
            In the limited circumstances where a refund may be applicable,
            please email our support team at{' '}
            <a
              href="mailto:contact@tekkscope.com"
              className="text-black dark:text-white"
            >
              contact@tekkscope.com
            </a>{' '}
            with the following information:
          </p>
          <ul className="my-3 list-disc pl-6">
            <li>Your registered email address</li>
            <li>Date of purchase</li>
            <li>Order ID or payment reference (if available)</li>
            <li>
              Detailed explanation of why you believe you qualify for a refund
              under our policy
            </li>
          </ul>
          <p>
            Our team will review your request and respond within 5 business
            days.
          </p>

          <h2 className="mb-3 mt-6 text-xl font-semibold">
            Processing of Refunds
          </h2>
          <p>If a refund is approved:</p>
          <ul className="my-3 list-disc pl-6">
            <li>
              Refunds will be issued using the original payment method used for
              the purchase.
            </li>
            <li>
              The time required for the refund to reflect in your account
              depends on your payment provider and may take 7-14 business days.
            </li>
            <li>
              Refunds typically process within 5-10 business days depending on
              your payment provider.
            </li>
          </ul>

          <h2 className="mb-3 mt-6 text-xl font-semibold">
            Changes to This Policy
          </h2>
          <p>
            We reserve the right to modify this policy at any time. Changes will
            be effective immediately upon posting on our website. It is your
            responsibility to review this policy periodically. Your continued
            use of our services after any changes indicates your acceptance of
            the updated policy.
          </p>

          <h2 className="mb-3 mt-6 text-xl font-semibold">Contact Us</h2>
          <p>
            If you have any questions about this Refund and Cancellation Policy,
            please contact us at:
          </p>
          <div className="mt-3">
            <p>
              <strong>Tekkscope</strong>
            </p>
            <p>
              Email:{' '}
              <a
                href="mailto:contact@tekkscope.com"
                className="text-black dark:text-white"
              >
                contact@tekkscope.com
              </a>
            </p>
          </div>
        </div>
      </Container>
      <Footer />
    </>
  );
};

export default RefundPolicyPage;
