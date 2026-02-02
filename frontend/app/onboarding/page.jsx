"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { supabase } from "@/Clients/supabase/client";
import {
  ChevronLeft,
  Search,
  Code,
  Briefcase,
  Building,
  Rocket,
  Users,
  Mic,
  Bot,
  Globe,
  MessageSquare,
  Phone,
  Settings,
} from "lucide-react";
import { useAuth } from "@/app/contexts/AuthContext";
import { toast } from "sonner";
import { InteractiveHoverButton } from "@/components/ui/get-started";

const questions = [
  {
    question: "Welcome! Where did you hear about us?",
    key: "source",
    options: [
      { text: "Google Search", icon: <Search /> },
      { text: "Youtube", icon: <Mic /> },
      { text: "Blog", icon: <MessageSquare /> },
      { text: "LinkedIn", icon: <Briefcase /> },
      { text: "Twitter", icon: <Bot /> },
      { text: "Discord", icon: <Globe /> },
      { text: "Friend", icon: <Users /> },
      { text: "Other", icon: <Settings /> },
    ],
    type: "multiple",
  },
  {
    question: "What is your role?",
    key: "role",
    options: [
      { text: "Developer", icon: <Code /> },
      { text: "Business User", icon: <Briefcase /> },
    ],
    type: "single",
  },
  {
    question: "What are you using Tekkscope for?",
    key: "usage",
    options: [
      { text: "Personal Project", icon: <Rocket /> },
      { text: "Enterprise", icon: <Building /> },
      { text: "Agency", icon: <Users /> },
      { text: "Startup", icon: <Rocket /> },
    ],
    type: "multiple",
  },
];

const Onboarding = () => {
  const { user } = useAuth();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [onboardingData, setOnboardingData] = useState({});
  const [onboardingStarted, setOnboardingStarted] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (user && user.onboarding) {
      router.push("/dashboard");
    }
  }, [user]);

  const handleAnswer = (optionText) => {
    const currentKey = questions[currentQuestion].key;
    const currentType = questions[currentQuestion].type;

    setOnboardingData((prevData) => {
      if (currentType === "multiple") {
        const existingAnswers = prevData[currentKey] || [];
        if (existingAnswers.includes(optionText)) {
          return {
            ...prevData,
            [currentKey]: existingAnswers.filter((item) => item !== optionText),
          };
        } else {
          return {
            ...prevData,
            [currentKey]: [...existingAnswers, optionText],
          };
        }
      } else {
        return { ...prevData, [currentKey]: optionText };
      }
    });

    if (currentType === "single") {
      setTimeout(() => nextQuestion(), 300);
    }
  };

  const nextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };

  const finishOnboarding = async () => {
    if (!user) {
      toast.error("You must be logged in to save your preferences.");
      return;
    }

    const welcomeNotification = {
          id: `welcome-${Date.now()}`,
          title: 'Welcome to Tekkscope!',
          message:
            'Welcome to Tekkscope! We are glad you are here. You can head to Playground to test Tekkscope models with your free credits. Enjoy!',
          time: new Date().toISOString(),
          read: false,
        };

    const { data, error } = await supabase
      .from("user_data")
      .update({ onboarding_data: onboardingData, onboarding: true, notifications:[welcomeNotification]  })
      .eq("uuid", user.uuid);

    const {data: creditsData, error: creditsError} = await supabase
    .from("credits")
    .upsert({
      user_id: user.uuid,
      balance: 1,
      last_updated: new Date().toISOString(),
    })

    if (error || creditsError) {
      console.error("Error updating onboarding data:", error);
      toast.error("Failed to save your preferences. Please try again.");
      return { error: "Failed to update onboarding data." };
    }

    toast.success("Your preferences have been saved.");
    router.push("/dashboard");
  };

  const progress = onboardingStarted
    ? ((currentQuestion + 1) / questions.length) * 100
    : 0;

  if (!onboardingStarted) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="min-h-screen w-full md:full bg-tekk-bg flex flex-col items-center justify-center p-4 sm:p-6 md:p-8"
      >
        <motion.section
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="max-w-5xl w-full mx-auto text-center"
        >
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-instrument text-white">
            Welcome {user?.name || "To Tekkscope"},
          </h1>
          <p className="text-base sm:text-lg text-gray-400 mt-2 font-inter">
            This will take just a minute.
          </p>

          <InteractiveHoverButton
            onClick={() => setOnboardingStarted(true)}
            onTap={() => router.push("/authentication")}
            className="bg-white text-black mt-4"
          >
            Get Started
          </InteractiveHoverButton>
        </motion.section>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="min-h-screen w-full md:w-full bg-tekk-bg flex flex-col items-center justify-center p-4 sm:p-6 md:p-8"
    >
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-2 bg-tekk-darkest z-50">
        <div
          className="h-2 bg-linear-to-r from-tekk-dark to-tekk-primary transition-all duration-500 ease-in-out"
          style={{ width: `${progress}%` }}
        ></div>
      </div>

      {/* Onboarding Question */}
      <motion.section
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="max-w-7xl w-full mx-auto"
      >
        <div className=" p-6 sm:p-8 rounded-xl">
          <h2 className="text-xl sm:text-2xl font-medium font-inter mb-6 text-white">
            {questions[currentQuestion].question}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {questions[currentQuestion].options.map((option) => {
              const isSelected =
                onboardingData[questions[currentQuestion].key] ===
                  option.text ||
                (Array.isArray(
                  onboardingData[questions[currentQuestion].key]
                ) &&
                  onboardingData[questions[currentQuestion].key].includes(
                    option.text
                  ));
              return (
                <button
                  key={option.text}
                  onClick={() => handleAnswer(option.text)}
                  className={`p-4 2xl:min-h-[100px] cursor-pointer border rounded-lg text-center transition-all duration-200 transform active:scale-95 flex items-center justify-center ${
                    isSelected
                      ? "bg-white text-black"
                      : "bg-tekk-darkest  border-tekk-darkest hover:border-tekk-dark  text-white"
                  }`}
                >
                  <div className="mr-4">{option.icon}</div>
                  {option.text}
                </button>
              );
            })}
          </div>
          <div className="mt-8 flex justify-between">
            <div>
              {currentQuestion > 0 && (
                <button
                  onClick={previousQuestion}
                  className="px-2 py-2 flex items-center group text-gray-400 hover:text-white"
                >
                  <ChevronLeft className="mr-2 group-hover:scale-105 transition-transform" />
                  Back
                </button>
              )}
            </div>
            <div className="grow text-right">
              {currentQuestion === questions.length - 1 ? (
                <InteractiveHoverButton
                  onClick={finishOnboarding}
                  onTap={finishOnboarding}
                  className="bg-white text-black mt-4"
                >
                  Finish
                </InteractiveHoverButton>
              ) : (
                <InteractiveHoverButton
                  onClick={nextQuestion}
                  onTap={nextQuestion}
                  className="bg-white text-black mt-4"
                >
                  Next
                </InteractiveHoverButton>
              )}
            </div>
          </div>
        </div>
      </motion.section>
    </motion.div>
  );
};

export default Onboarding;
