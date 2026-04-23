import { Modal } from '../../../shared/components/Modal';

export function TermsModal({ isOpen, onClose }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Terms and Conditions" size="2xl">
      <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
        <section>
          <h3 className="font-semibold text-gray-800 mb-2">1. Acceptance of Terms</h3>
          <p>
            By accessing and using OptiCV, you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">2. Use License</h3>
          <p className="mb-2">
            Permission is granted to temporarily download one copy of the materials (information or software) on OptiCV for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Modifying or copying the materials</li>
            <li>Using the materials for any commercial purpose or for any public display</li>
            <li>Attempting to decompile or reverse engineer any software contained on OptiCV</li>
            <li>Removing any copyright or other proprietary notations from the materials</li>
            <li>Transferring the materials to another person or "mirroring" the materials on any other server</li>
          </ul>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">3. Disclaimer</h3>
          <p>
            The materials on OptiCV are provided on an 'as is' basis. OptiCV makes no warranties, expressed or implied, and hereby disclaims and negates all other warranties including, without limitation, implied warranties or conditions of merchantability, fitness for a particular purpose, or non-infringement of intellectual property or other violation of rights.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">4. Limitations</h3>
          <p>
            In no event shall OptiCV or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on OptiCV, even if OptiCV or an authorized representative has been notified orally or in writing of the possibility of such damage.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">5. Accuracy of Materials</h3>
          <p>
            The materials appearing on OptiCV could include technical, typographical, or photographic errors. OptiCV does not warrant that any of the materials on its website are accurate, complete, or current. OptiCV may make changes to the materials contained on its website at any time without notice.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">6. User Responsibilities</h3>
          <p>
            Users are responsible for maintaining the confidentiality of their account information and password. Users are responsible for all activities that occur under their account. Users agree to notify OptiCV immediately of any unauthorized use of their account.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">7. Governing Law</h3>
          <p>
            These terms and conditions are governed by and construed in accordance with the laws of Spain, and you irrevocably submit to the exclusive jurisdiction of the courts in that location.
          </p>
        </section>

        <section>
          <h3 className="font-semibold text-gray-800 mb-2">8. Privacy Policy</h3>
          <p>
            Your use of OptiCV is also governed by our Privacy Policy. Please review our Privacy Policy to understand our practices.
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
