"use client";

const plans = [
  {
    name: "Free",
    price: 0,
    description: "Try Munesh AI with zero commitment — perfect for exploring",
    features: [
      "1 AI Agent (Chat only)",
      "50 messages/month",
      "Basic CRM",
      "WhatsApp integration",
      "Community support",
    ],
    notIncluded: [
      "Sales/Support/Booking agents",
      "Analytics dashboard",
      "Follow-up sequences",
      "Self-improvement AI",
      "API access",
    ],
    cta: "Get Started Free",
    popular: false,
    color: "gray",
  },
  {
    name: "Starter",
    price: 49,
    description: "Perfect for small businesses getting started with AI automation",
    features: [
      "1 AI Agent (Chat or Sales)",
      "500 messages/month",
      "Basic CRM & lead tracking",
      "WhatsApp integration",
      "Email support",
      "Basic analytics dashboard",
    ],
    notIncluded: [
      "Multi-agent system",
      "Self-improvement AI",
      "Advanced analytics",
      "API access",
    ],
    cta: "Start Free Trial",
    popular: false,
    color: "blue",
  },
  {
    name: "Pro",
    price: 149,
    description: "For growing businesses that want full AI-powered automation",
    features: [
      "4 AI Agents (Chat, Sales, Support, Booking)",
      "Unlimited messages",
      "Full CRM with lead scoring",
      "WhatsApp integration",
      "Daily Loop automation",
      "Self-Improvement AI Agent",
      "Performance Analyzer",
      "Advanced analytics & reports",
      "Priority support",
      "Automated follow-up sequences",
    ],
    notIncluded: [
      "Custom AI agents",
      "API access",
      "White-label",
    ],
    cta: "Start Free Trial",
    popular: true,
    color: "indigo",
  },
  {
    name: "Enterprise",
    price: 499,
    description: "For teams that need custom AI agents and full platform control",
    features: [
      "Everything in Pro",
      "Custom AI agents",
      "Full API access",
      "White-label dashboard",
      "Dedicated account manager",
      "Custom integrations",
      "SLA guarantee (99.9% uptime)",
      "Advanced security & compliance",
      "Multi-number WhatsApp support",
      "Custom analytics & reporting",
    ],
    notIncluded: [],
    cta: "Contact Sales",
    popular: false,
    color: "purple",
  },
];

const faqs = [
  {
    q: "How does the free trial work?",
    a: "You get 14 days of full access to your chosen plan. No credit card required. If you love it, upgrade seamlessly. If not, no worries.",
  },
  {
    q: "Can I switch plans later?",
    a: "Absolutely! Upgrade or downgrade anytime. Changes take effect immediately, and we'll prorate the difference.",
  },
  {
    q: "What happens if I exceed my message limit?",
    a: "On the Free plan, you're limited to 50 messages/month. On Starter, additional messages beyond 500 are $0.05 each. Pro and Enterprise have unlimited messages included.",
  },
  {
    q: "Do I need technical knowledge to set this up?",
    a: "Not at all. Connect your WhatsApp Business account, and our AI agents start working immediately. Setup takes under 10 minutes.",
  },
  {
    q: "How does the Self-Improvement AI work?",
    a: "Our AI analyzes every conversation to identify what works. It automatically optimizes prompts, follow-up timing, and sales strategies — getting smarter every day without any manual work.",
  },
];

export default function PricingPage() {
  return (
    <div>
      {/* Header */}
      <div className="text-center mb-10">
        <h2 className="text-3xl font-bold text-gray-900">
          Simple, Transparent Pricing
        </h2>
        <p className="text-gray-500 mt-2 text-lg">
          Start free. Scale as you grow. No hidden fees.
        </p>
        <div className="mt-3 inline-block bg-green-100 text-green-800 text-sm font-medium px-3 py-1 rounded-full">
          14-day free trial on all plans
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`bg-white rounded-xl shadow-sm border-2 p-6 relative flex flex-col ${
              plan.popular
                ? "border-indigo-500 ring-2 ring-indigo-200"
                : "border-gray-200"
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-indigo-600 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                  Most Popular
                </span>
              </div>
            )}

            <div className="mb-4">
              <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
              <p className="text-sm text-gray-500 mt-1">{plan.description}</p>
            </div>

            <div className="mb-6">
              {plan.price === 0 ? (
                <>
                  <span className="text-4xl font-bold text-gray-900">Free</span>
                  <span className="text-gray-500 text-sm"> forever</span>
                </>
              ) : (
                <>
                  <span className="text-4xl font-bold text-gray-900">
                    ${plan.price}
                  </span>
                  <span className="text-gray-500 text-sm">/month</span>
                </>
              )}
            </div>

            <button
              className={`w-full py-3 px-4 rounded-lg font-semibold text-sm mb-6 transition-colors ${
                plan.popular
                  ? "bg-indigo-600 text-white hover:bg-indigo-700"
                  : "bg-gray-100 text-gray-800 hover:bg-gray-200"
              }`}
            >
              {plan.cta}
            </button>

            <div className="flex-1">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                What&apos;s included
              </p>
              <ul className="space-y-2">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start text-sm">
                    <span className="text-green-500 mr-2 mt-0.5 flex-shrink-0">
                      &#10003;
                    </span>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              {plan.notIncluded.length > 0 && (
                <>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mt-4 mb-3">
                    Not included
                  </p>
                  <ul className="space-y-2">
                    {plan.notIncluded.map((feature) => (
                      <li key={feature} className="flex items-start text-sm">
                        <span className="text-gray-300 mr-2 mt-0.5 flex-shrink-0">
                          &#10007;
                        </span>
                        <span className="text-gray-400">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Social Proof */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-8 mb-12 text-center">
        <h3 className="text-lg font-bold text-gray-900 mb-4">
          Trusted by Growing Businesses
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="text-3xl font-bold text-indigo-600">3x</div>
            <div className="text-sm text-gray-600">More demo bookings</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-indigo-600">40%</div>
            <div className="text-sm text-gray-600">Faster response times</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-indigo-600">60%</div>
            <div className="text-sm text-gray-600">Higher conversion rate</div>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="mb-8">
        <h3 className="text-xl font-bold text-gray-900 mb-6 text-center">
          Frequently Asked Questions
        </h3>
        <div className="space-y-4 max-w-2xl mx-auto">
          {faqs.map((faq) => (
            <div
              key={faq.q}
              className="bg-white rounded-lg border border-gray-200 p-5"
            >
              <h4 className="font-semibold text-gray-900 mb-2">{faq.q}</h4>
              <p className="text-sm text-gray-600">{faq.a}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="text-center bg-white rounded-xl border border-gray-200 shadow-sm p-8">
        <h3 className="text-xl font-bold text-gray-900 mb-2">
          Ready to automate your WhatsApp business?
        </h3>
        <p className="text-gray-500 mb-4">
          Start your 14-day free trial today. No credit card required.
        </p>
        <button className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors">
          Get Started Free
        </button>
      </div>
    </div>
  );
}
