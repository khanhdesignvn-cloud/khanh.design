import HkmQuotes from '../hkm-quotes';
import LoginScreen from '../login-screen';
import {adminSession} from '../admin';
export const dynamic='force-dynamic';
export default async function Page(){const {isAdmin}=await adminSession();return isAdmin?<HkmQuotes/>:<LoginScreen/>;}
