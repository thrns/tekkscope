import React from 'react';

const PrivacyPolicy = () => {
  return (
    <div className="min-h-screen w-full bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 className='text-3xl font-bold mb-4'>Privacy Policy (Project Demo)</h1>
        <p className='mb-4'>Effective Date: Project demo release</p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>1. Introduction</h2>
        <p>
          Tekkscope is a portfolio project. This notice explains the categories of information the demo may process when enabled by a deployment. A production launch should replace this notice with a jurisdiction-specific policy reviewed by the deployment owner.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>2. Information We Collect</h2>
        <p>
          We may collect information about you in a variety of ways. The information we may collect includes:
        </p>
        <ul className='list-disc list-inside ml-4 mt-2'>
          <li>
            <strong>Personal Data:</strong> Personally identifiable information, such as your name, shipping address, email address, and telephone number, and demographic information, such as your age, gender, hometown, and interests, that you voluntarily give to us when you register with our service or when you choose to participate in various activities related to the service.
          </li>
          <li>
            <strong>Financial Data:</strong> This portfolio demo does not currently process payments. A production deployment should document its payment processor separately.
          </li>
        </ul>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>3. Use of Your Information</h2>
        <p>
          Having accurate information about you permits us to provide you with a smooth, efficient, and customized experience. Specifically, we may use information collected about you to:
        </p>
        <ul className='list-disc list-inside ml-4 mt-2'>
          <li>Create and manage your account.</li>
          <li>Process your transactions and send you related information, including purchase confirmations and invoices.</li>
          <li>Email you regarding your account or order.</li>
          <li>Improve our website and services.</li>
        </ul>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>4. Disclosure of Your Information</h2>
        <p>
          We may share information we have collected about you in certain situations. Your information may be disclosed as follows:
        </p>
        <ul className='list-disc list-inside ml-4 mt-2'>
          <li>
            <strong>By Law or to Protect Rights:</strong> If we believe the release of information about you is necessary to respond to legal process, to investigate or remedy potential violations of our policies, or to protect the rights, property, and safety of others, we may share your information as permitted or required by any applicable law, rule, or regulation.
          </li>
          <li>
            <strong>Third-Party Service Providers:</strong> We may share your information with third parties that perform services for us or on our behalf, including payment processing, data analysis, email delivery, hosting services, customer service, and marketing assistance.
          </li>
        </ul>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>5. Security of Your Information</h2>
        <p>
          We use administrative, technical, and physical security measures to help protect your personal information. While we have taken reasonable steps to secure the personal information you provide to us, please be aware that despite our efforts, no security measures are perfect or impenetrable, and no method of data transmission can be guaranteed against any interception or other type of misuse.
        </p>

        <h2 className='text-2xl font-semibold mt-6 mb-2'>6. Contact Us</h2>
        <p>
          If you have questions or comments about this Privacy Policy, please contact us at:
        </p>
        <p className='mt-2'>
          Tekkscope Project<br />
          See the repository owner&apos;s project contact channel.
        </p>
      </div>
    </div>
  );
};

export default PrivacyPolicy;
