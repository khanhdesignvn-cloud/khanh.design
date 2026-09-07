import Workspace from './workspace';
import {adminSession} from './admin';
import {chatGPTSignInPath,chatGPTSignOutPath} from './chatgpt-auth';
export const dynamic='force-dynamic';
export default async function Page(){const {user,isAdmin}=await adminSession();return <Workspace isAdmin={isAdmin} signedIn={!!user} signInHref={chatGPTSignInPath('/')} signOutHref={chatGPTSignOutPath('/')}/>;}
