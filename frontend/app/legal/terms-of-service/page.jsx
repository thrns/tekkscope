import React from 'react';

const TermsOfService = () => {
  return (
    <div className="min-h-screen w-full bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 className='text-3xl font-bold mb-4'>Terms of Service (Project Demo)</h1>
        <p className='mb-4'>Effective Date: Project demo release</p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>1. Agreement to Terms</h2>
        <p>
          By using our services, you agree to be bound by these Terms of Service. If you do not agree to these terms, please do not use our services.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>2. Changes to Terms or Services</h2>
        <p>
          We may modify the terms at any time. If we do so, we’ll let you know either by posting the modified terms on the site or through other communications. It’s important that you review the terms whenever we modify them because if you continue to use the services after we have posted modified terms on the site, you are indicating to us that you agree to be bound by the modified terms.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>3. Who May Use the Services</h2>
        <p>
          You may use the services only if you are 18 years or older and are not barred from using the services under applicable law.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>4. Privacy Policy</h2>
        <p>
          Our Privacy Policy describes how we handle the information you provide to us when you use our services. You understand that through your use of the services you consent to the collection and use (as set forth in the Privacy Policy) of this information.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>5. Content on the Services</h2>
        <p>
          You are responsible for your use of the services and for any content you provide, including compliance with applicable laws, rules, and regulations. You should only provide content that you are comfortable sharing with others.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>6. Payments</h2>
        <p>
          We use a third-party payment processor to bill you through a payment account linked to your account on the services. The processing of payments will be subject to the terms, conditions, and privacy policies of the payment processor in addition to this Agreement.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>7. Contact Us</h2>
        <p>
          If you have any questions about these Terms, please contact us at:
        </p>
        <p className='mt-2'>
          Tekkscope Project<br />
          Portfolio demonstration; no business address is published here.<br />
          Contact the repository owner through the project contact channel.
        </p>
      </div>
    </div>
  );
};

export default TermsOfService;
