import React from "react";
import {
  Facebook,
  Instagram,
  Linkedin,
  Send,
  ChevronRight,
  Mail,
} from "lucide-react";
import Image from "next/image";

const Footer = () => {
  return (
    <footer className="py-12 md:py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
          {/* Logo and Socials */}
          <div className="space-y-6">
            <div className="flex items-center justify-start">
              <Image
                src="/logos/icon.png"
                alt="Tekkscope Logo"
                width={45}
                height={45}
              />
              <span className="font-instrument text-3xl text-primary-tekk-heading">
                Tekkscope.
              </span>
            </div>
            <p className="text-gray-600 text-sm md:text-base">
              Aanalyze sources, synthesize insights, and
              get structured research reports, all via a simple API call.
            </p>
            <div className="flex space-x-3">
              <a
                href="#"
                className="text-primary-tekk border border-gray-300 hover:text-gray-700 bg-white rounded-full p-2 "
              >
                <Facebook size={20} />
              </a>
              <a
                href="https://linkedin.com/company/tekkscope"
                className="text-primary-tekk border border-gray-300 hover:text-gray-700 bg-white rounded-full p-2 "
              >
                <Linkedin size={20} />
              </a>
              <a
                href="https://instagram.com/tekkscope"
                className="text-primary-tekk border border-gray-300 hover:text-gray-700 bg-white rounded-full p-2 "
              >
                <Instagram size={20} />
              </a>
              <a
                href="https://www.tekkscope.com/"
                className="text-primary-tekk border border-gray-300 hover:text-gray-700 bg-white rounded-full p-2 "
              >
                <Mail size={20} />
              </a>
            </div>
          </div>

          {/* Company Links */}
          <div className="md:justify-self-center">
            <h3 className="text-lg font-bold text-gray-800">Company</h3>
            <ul className="mt-5 space-y-3">
              <li>
                <a
                  href="#"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  Home
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  About us
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  Pricing
                </a>
              </li>
            </ul>
          </div>

          {/* Product Links */}
          <div className="md:justify-self-center">
            <h3 className="text-lg font-bold text-gray-800">Product</h3>
            <ul className="mt-5 space-y-3">
              <li>
                <a
                  href="#"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  Features
                </a>
              </li>
              <li>
                <a
                  href="#"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  How It Works
                </a>
              </li>
              <li>
                <a
                  href="/legal/privacy-policy"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  Privacy Policy
                </a>
              </li>
              <li>
                <a
                  href="/legal/terms-of-service"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  Terms of Service
                </a>
              </li>
              <li>
                <a
                  href="/legal/refund-policy"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  Refund Policy
                </a>
              </li>
              <li>
                <a
                  href="/legal/contact-us"
                  className="text-base text-gray-600 hover:text-gray-900"
                >
                  Contact Us
                </a>
              </li>
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h3 className="text-lg font-bold text-gray-800">Newsletter</h3>
            <p className="mt-5 text-sm md:text-base text-gray-600">
              Get the latest news and insights on AI-powered research and product updates from Tekkscope.
            </p>
            <form className="mt-5">
              <div className="flex flex-row justify-center items-center bg-white border border-gray-200 rounded-full shadow-sm p-1 pr-2">
                <input
                  type="email"
                  required
                  className="appearance-none w-full bg-transparent border-none rounded-full py-2 px-4 text-base text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-0"
                  placeholder="Email address"
                />
                <button
                  type="submit"
                  className="bg-tekk-primary  sm:w-auto flex items-center justify-center border border-transparent rounded-full py-2 px-4 text-sm font-medium text-white"
                >
                  Subscribe <ChevronRight size={16} />
                </button>
              </div>
            </form>
          </div>
        </div>

        <div className="mt-16 border-t border-gray-200 pt-8 flex flex-col md:flex-row md:items-center md:justify-between">
          <p className="text-sm text-gray-500 md:order-1">&copy; 2025 Tekkscope. All rights reserved.</p>
          <p className="text-sm text-gray-500 mt-2 md:mt-0 md:order-2">Product of Astrapi Money PVT LTD, Chennai, Tamil Nadu, India</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
