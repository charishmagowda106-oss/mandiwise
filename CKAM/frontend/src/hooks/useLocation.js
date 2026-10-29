// The farmer's location is now shared app-wide (header picker + every page),
// so the logic lives in LocationContext. This re-export keeps page imports stable.
export { default } from '../context/LocationContext';
