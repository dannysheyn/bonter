import logo from './bot_logo_crop.jpg';

const Sidebar = () => {
    const avatarWidth = 80;
    const avatarHight = 80;
    const alt = 'bot logo';

    return (
        <div>
            <nav className="sidebar">
                <img src={logo} alt={alt} width={avatarWidth} hight={avatarHight}/>
                <div className="links">
                    <a href="/">Home</a>
                    <a href="/">Build</a>
                    <a href="/">Dashboard</a>
                </div>
            </nav>
        </div>
    );
}

export default Sidebar;