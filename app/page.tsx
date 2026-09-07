import Workspace from './workspace';
import {adminSession} from './admin';
export const dynamic='force-dynamic';
export default async function Page(){const {isAdmin}=await adminSession();return <Workspace isAdmin={isAdmin}/>;}
