import { NavLink } from 'react-router-dom';
import './Navbar.css';

export default function Navbar() {
    return (
        <nav className="navbar">
            <div className="navbar-inner container">
                <NavLink to="/" className="navbar-brand">
                    <span className="brand-icon">⚡</span>
                    <span className="brand-text">OpenOA</span>
                    <span className="brand-tag">Analytics</span>
                </NavLink>

                <div className="navbar-links">
                    <NavLink to="/" end className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        Dashboard
                    </NavLink>
                    <NavLink to="/data" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        Data
                    </NavLink>
                    <NavLink to="/analysis" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>
                        Analysis
                    </NavLink>
                </div>
            </div>
        </nav>
    );
}
