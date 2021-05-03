import logo from '../bot_logo_crop.jpg';
import React from 'react'
import { useHistory, useLocation } from 'react-router-dom';
import Drawer from '@material-ui/core/Drawer';
import Typography from '@material-ui/core/Typography';
import { makeStyles } from '@material-ui/core';
import List from '@material-ui/core/List';
import ListItem from '@material-ui/core/ListItem';
import ListItemIcon from '@material-ui/core/ListItemIcon';
import ListItemText from '@material-ui/core/ListItemText';
import HomeIcon from '@material-ui/icons/Home';
import BuildIcon from '@material-ui/icons/Build';
import DashboardIcon from '@material-ui/icons/Dashboard';


const drawerWidth = 220;

const useStyles = makeStyles({
    drawer :{
        width: drawerWidth,
    },
    drawerPaper :{
        width: drawerWidth,
    },
    root:{
        display: 'flex'
    },
    active:{
        background: '#f4f4f4'
    }
})


const Sidebar = () => {
    const avatarWidth = 80;
    const avatarHeight = 100;
    const alt = 'bot logo';
    const classes = useStyles();
    //const location = useLocation();
    const navbarLinks = [
    {
        text: 'Home',
        icon: <HomeIcon/>,
        path: '/'    
    }, 
    {
        text: 'Build',
        icon: <BuildIcon/>,
        path: '/build'
    },
    {   
        text: 'Dashboard',
        icon: <DashboardIcon/>,
        path: '/dashboard'
    }
    ]

    return (
        <div className={classes.root}>
            <Drawer
            className={classes.drawer}
            variant='permanent'
            anchor='left'
            classes={{ paper: classes.drawerPaper}}
            >
                <div>
                    <Typography variant='h5'>
                        Build
                    </Typography>
                </div>
            <List>
               {navbarLinks.map((item) => {return (
               <ListItem 
                key={item.text} 
                button
                //component='a'
                href={item.path}
                >
                    <ListItemIcon>
                        {item.icon}
                    </ListItemIcon>
                    <ListItemText primary={item.text}/>
                </ListItem>)
               })}
            </List>
            </Drawer>
            
        </div>
    );
}

export default Sidebar;

// {/* <nav className="sidebar">
//                 <img src={logo} alt={alt} width={avatarWidth} height={avatarHeight}/>
//                 <div className="links">
//                     <a href="/">Home</a>
//                     <a href="/">Build</a>
//                     <a href="/">Dashboard</a>
//                 </div>
//             </nav> */}