import { Modal } from '../../../shared/components/Modal';

export function PrivacyModal({ isOpen, onClose }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Privacy Policy" size="2xl">
      <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
        <section>
          <h3 className="font-semibold text-gray-800 mb-2">1. Introduction</h3>
          <p>
            OptiCV ("we" or "us" or "our") operates the OptiCV website. This page informs you of our policies regarding the collection, use, and disclosure of personal data when you use our service and the choices you have associated with that data.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">2. Information Collection and Use</h3>
          <p>We collect several different types of information for various purposes to provide and improve our service to you.</p>
          <ul className="list-disc pl-5 mt-2 space-y-1">
            <li><strong>Personal Data:</strong> While using our service, we may ask you to provide us with certain personally identifiable information that can be used to contact or identify you ("Personal Data"). This may include:
              <ul className="list-circle pl-5 mt-1 space-y-1">
                <li>Email address</li>
                <li>First and last name</li>
                <li>Cookies and Usage Data</li>
              </ul>
            </li>
            <li><strong>CV Data:</strong> When you upload your CV, we store it securely for analysis purposes only.</li>
          </ul>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">3. Use of Data</h3>
          <p>OptiCV uses the collected data for various purposes:</p>
          <ul className="list-disc pl-5 mt-2 space-y-1">
            <li>To provide and maintain our service</li>
            <li>To notify you about changes to our service</li>
            <li>To allow you to participate in interactive features</li>
            <li>To gather analysis or valuable information for improvement</li>
            <li>To monitor the usage of our service</li>
            <li>To detect, prevent and address technical issues</li>
          </ul>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">4. Security of Data</h3>
          <p>
            The security of your data is important to us, but remember that no method of transmission over the Internet or method of electronic storage is 100% secure. While we strive to use commercially acceptable means to protect your Personal Data, we cannot guarantee its absolute security.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">5. Children's Privacy</h3>
          <p>
            Our service does not address anyone under the age of 18 ("Children"). We do not knowingly collect personally identifiable information from children. If you become aware that a child has provided us with personal data, please contact us immediately.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">6. Changes to This Privacy Policy</h3>
          <p>
            We may update our privacy policy from time to time. We will notify you of any changes by posting the new privacy policy on this page and updating the "effective date" at the bottom of this policy.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">7. Contact Us</h3>
          <p>
            If you have any questions about this privacy policy, please contact us at privacy@opticv.com
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">8. Data Retention</h3>
          <p>
            We will retain your personal data only for as long as necessary for the purposes set out in this privacy policy. We will retain and use your personal data to the extent necessary to comply with our legal obligations.
          </p>
        </section>

        <section className="pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </section>
      </div>
    </Modal>
  );
}
