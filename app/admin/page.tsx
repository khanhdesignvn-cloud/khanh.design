import Workspace from '../workspace';
import LoginScreen from '../login-screen';
import {adminSession} from '../admin';
export const dynamic='force-dynamic';
export default async function Page(){const {isAdmin}=await adminSession();return isAdmin?<Workspace isAdmin={true}/>:<LoginScreen/>;}
