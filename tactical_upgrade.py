from pathlib import Path
from datetime import datetime
import shutil, sys

p = Path("index.html")
s = p.read_text()
backup = Path("index_backup_tactics_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".html")
shutil.copy2(p, backup)

def section(start, end, replacement, label):
    global s
    a = s.find(start)
    b = s.find(end, a + len(start)) if a >= 0 else -1
    if a < 0 or b < 0:
        sys.exit(f"Stopped safely: could not locate {label}. Backup: {backup.name}")
    s = s[:a] + replacement + "\n" + s[b:]
    print("Updated:", label)

section(
"function teamAI(p,team,dt){",
"function ai(dt){",
"""function teamAI(p,team,dt){
 const homeSide=team==='home';
 const dir=homeSide?-1:1;
 const mates=homeSide?[you,...home]:[cpu,...away];
 const rivals=homeSide?[cpu,...away]:[you,...home];
 const bx=ball.position.x,bz=ball.position.z;
 const dBall=q=>Math.hypot(q.g.position.x-bx,q.g.position.z-bz);
 const closest=[...mates].sort((a,b)=>dBall(a)-dBall(b))[0];
 const rivalClosest=[...rivals].sort((a,b)=>dBall(a)-dBall(b))[0];
 const ourTeamHasBall=dBall(closest)<dBall(rivalClosest)+1.2;
 let tx=p.homeX,tz=p.homeZ;

 // Compact defensive line and coordinated forward movement.
 const ballShift=clamp(bz*.20,-8,8);
 tz+=ballShift;
 tx+=clamp(bx*.22,-6,6);

 if(p.role==='DEF'){
  // Defenders protect the goal and squeeze forward only when safe.
  tz+=dir*clamp((Math.abs(bz)-12)*.20,-2,7);
  if(!ourTeamHasBall&&Math.abs(bz)<28)tx+=clamp((bx-p.homeX)*.16,-4,4);
 }else if(p.role==='MID'){
  // Midfielders offer passing angles around the ball.
  tz+=dir*(ourTeamHasBall?4:0);
  tx+=clamp((bx-p.homeX)*.22,-7,7);
 }else{
  // Forwards make runs into space instead of crowding the ball.
  tz+=dir*(ourTeamHasBall?9:3);
  tx+=clamp((bx-p.homeX)*.12,-5,5);
 }

 // One player presses the ball; teammates hold their tactical shape.
 if(p===closest){
  tx=bx;tz=bz;
 }else if(!ourTeamHasBall&&p.role==='MID'&&dBall(p)<11){
  tx=bx;tz=bz+dir*2;
 }

 tx=clamp(tx,-26,26);
 tz=clamp(tz,-42,42);
 const v=new THREE.Vector3(tx-p.g.position.x,0,tz-p.g.position.z);
 if(v.length()>1)v.normalize();
 movePlayer(p,v.x,v.z,dt,false);

 // If a supporting player has the ball, choose a sensible action.
 if(dBall(p)<1.45&&ball.position.y<1.1){
  const goalZ=homeSide?-46:46;
  const distanceToGoal=Math.abs(goalZ-ball.position.z);
  const centered=Math.abs(ball.position.x)<13;
  if(distanceToGoal<21&&centered){
   kick(p,14,.16,false);
  }else{
   const forwardMate=mates
    .filter(q=>q!==p&&((q.g.position.z-p.g.position.z)*dir>2))
    .sort((a,b)=>a.g.position.distanceTo(p.g.position)-b.g.position.distanceTo(p.g.position))[0];
   if(forwardMate&&Math.random()<dt*1.8)kick(p,9,.04,true);
   else if(Math.random()<dt*.7)kick(p,11,.08,false);
  }
 }
}""",
"coordinated team AI"
)

section(
"function kick(p,power,lift=0,pass=false){",
"function shoot(){",
"""function kick(p,power,lift=0,pass=false){
 const isHome=(p===you||home.includes(p));
 const dir=isHome?-1:1;
 let aim=new THREE.Vector3(0,0,dir);
 if(pass){
  const mates=isHome?[you,...home]:[cpu,...away];
  const options=mates.filter(q=>q!==p&&((q.g.position.z-p.g.position.z)*dir>1));
  options.sort((a,b)=>{
   const score=q=>Math.abs(q.g.position.x-ball.position.x)*.35+
     Math.abs(q.g.position.z-ball.position.z)*.20-
     ((q.g.position.z-p.g.position.z)*dir)*.15;
   return score(a)-score(b);
  });
  if(options.length){
   aim.copy(options[0].g.position).sub(ball.position);
   aim.y=0;
  }else{
   aim.x=clamp(-p.g.position.x*.025,-.3,.3);
  }
 }else{
  aim.x=clamp(-p.g.position.x*.025,-.3,.3);
 }
 aim.y=lift;
 aim.normalize();
 ballVel.copy(aim).multiplyScalar(power);
 ballVel.y=Math.max(ballVel.y,lift*power);
 ball.position.x=p.g.position.x+p.face.x*.85;
 ball.position.z=p.g.position.z+p.face.z*.85;
 ball.position.y=.52;
 p.hasBall=false;
 show(pass?'PASS!':'SHOT!');
}""",
"team-aware passing and shooting"
)

p.write_text(s)
print("\\nSUCCESS: tactical AI and team-aware passing installed.")
print("Backup:", backup.name)
