import React from 'react';

const ContactUs = () => {
  return (
    <div className="min-h-screen w-full bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white p-6 rounded-lg shadow-md">
        <h1 className='text-3xl font-bold mb-4'>Contact Us</h1>
        <p className='mb-4'>
          If you have any questions or concerns, please feel free to contact us using the information below.
        </p>

        <div className='mt-6'>
          <h2 className='text-2xl font-semibold'>Tekkscope Project</h2>
          <p className='mt-2'>
            This is a portfolio project and does not publish a business address.<br />
            Please use the repository owner&apos;s project contact channel.<br />
          </p>
          <p className='mt-4'>
            <strong>Email:</strong> See the repository owner&apos;s contact details<br />
            <strong>Phone:</strong> Not published for this portfolio demo
          </p>
        </div>
      </div>
    </div>
  );
};

export default ContactUs;
