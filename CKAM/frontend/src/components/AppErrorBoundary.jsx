import React from 'react';

export default class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return <main className="grid min-h-screen place-items-center bg-[#f8f6ec] p-5 text-center">
        <section className="mw-panel max-w-md p-8">
          <h1 className="text-2xl font-bold text-[#15261a]">We could not open your dashboard</h1>
          <p className="mt-3 text-gray-600">Refresh the page once. If the problem continues, log out and sign in again.</p>
          <button className="mw-button mt-6" onClick={() => window.location.assign('/login')}>Back to login</button>
        </section>
      </main>;
    }
    return this.props.children;
  }
}
