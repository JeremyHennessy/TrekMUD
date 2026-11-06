/* Original USS Asteria · bridge room 01 · sculpted practical-set furniture.
   Does not control movement, gameplay, access, or the approved ship topology. */
'use strict';
window.AsteriaFurniture=Object.freeze({
  chair({x,z,rot=0,large=false},api){
    const {box,cyl,ellipse,plane,tube,ring}=api;
    const sin=Math.sin,cos=Math.cos,PI=Math.PI;
    const co=cos(rot),si=sin(rot);
    const T=(dx,y,dz)=>[x+dx*co-dz*si,y,z+dx*si+dz*co];
    const B=(dx,y,dz,w,h,d,c,m=0)=>{const p=T(dx,y,dz);box(p[0],p[1],p[2],w,h,d,c,m,rot)};
    const L=(p,r,c,m=4,n=10)=>tube(p.map(t=>T(...t)),r,c,m,n);
    const LW=(worldPoints,r,c,m=4,n=10)=>tube(worldPoints,r,c,m,n);
    const h=large?1.12:.97;
    const w=large?.49:.42;
    const upholstery=large?0x857283:0x897782;
    const leather=large?0x9d8894:0xa3949e;
    // Cast circular base with floor-resistant broad feet, swivel column and bearing.
    cyl(x,.115,z,.30,.29,.17,0x54515a,3,42);
    cyl(x,.220,z,.225,.215,.09,0xb1a2a0,4,40);
    cyl(x,.365,z,.090,.090,.28,0x777681,4,26);
    cyl(x,.500,z,.162,.155,.08,0x34353f,7,32);
    for(let s of [-1,1]){
      B(s*.21,.20,.055,.22,.054,.085,0x787480,3);
      B(s*.26,.17,-.04,.18,.032,.24,0x555462,4);
    }
    // Upholstered molded seat: rounded horizontal outline, contrasting piping,
    // upper cushion and supporting seat pan (no rectangular stacked slabs).
    cyl(x,.665,z-.045,w+.075,.415,.18,0x4a4550,4,52);
    cyl(x,.730,z-.09,w,.37,.16,upholstery,5,56);
    ellipse(x,.818,z-.090,w*.965,.32,leather,5,64);
    ring(x,.825,z-.090,w,.352,.945,0x6e5c6a,4,64);
    for(let s of [-1,1]){
      B(s*(w-.045),.775,-.055,.032,.045,.48,0x695c68,4);
    }
    // A shaped back shell built from continuous cross-sections instead of cubes.
    // Rounded shoulders, tapered lumbar and a slightly swept-back crest.
    const rows=25,cols=22;
    const back=(t,u,side)=>{
      const y=.81+t*h;
      const half=w*(.82+.21*sin(PI*t)-.11*t);
      const dx=half*u;
      const camber=.085*(1-u*u);
      const dz=.245+.245*t+.055*sin(PI*t)-camber + side*(.052+.012*sin(PI*t));
      return T(dx,y,dz);
    };
    for(let i=0;i<rows;i++){
      const t=i/rows,t2=(i+1)/rows;
      for(let j=0;j<cols;j++){
        const u=-1+2*j/cols,v=-1+2*(j+1)/cols;
        // Rear molded shell, seen as a continuous contour from the aft entrance.
        plane(back(t,u,1),back(t,v,1),back(t2,v,1),back(t2,u,1),0x66606d,4);
        // Independent cushioned front face.
        plane(back(t2,u,-1),back(t2,v,-1),back(t,v,-1),back(t,u,-1),upholstery,5);
      }
    }
    for(let s of [-1,1]){
      const edge=[];
      const inner=[];
      for(let i=0;i<=36;i++){
        const t=i/36;
        edge.push(back(t,s,1));
        inner.push(back(t,s,-1));
      }
      LW(edge,.030,0x9c898e,4,8);
      LW(inner,.018,0xb49da8,4,8);
      for(let i=0;i<36;i++){
        plane(edge[i],inner[i],inner[i+1],edge[i+1],0x766776,4);
      }
    }
    // Shape lines across the upholstery, hand-finished stitch pattern.
    for(let v of [-.46,-.17,.17,.46]){
      const points=[];
      for(let j=0;j<=18;j++){
        const t=.09+j*.048;
        points.push(back(t,v,-1).map((p,i)=>i===2?p-.007:p));
      }
      LW(points,.006,0xb6a1ad,4,5);
    }
    for(let t of [.25,.49,.73,.91]){
      const marks=[];
      for(let j=0;j<=16;j++)marks.push(back(t,-.60+j*.075,-1));
      LW(marks,.006,0x766270,4,5);
    }
    // Leather-wrapped headrest, shaped shoulder cap and concealed attachment.
    cyl(...(p=>[p[0],p[1],p[2]])(T(0,.81+h-.05,.49)),w*.77,.105,.075,0x6c5d6b,4,36);
    L([[-w*.66,.82+h,.49],[0,.835+h,.515],[w*.66,.82+h,.49]],.017,0xb29d9c,4,8);
    // Freestanding, sculpted arm bars with subtle indicator controls.
    for(let s of [-1,1]){
      L([[s*(w+.125),.56,-.18],[s*(w+.12),.88,-.17],[s*(w+.12),.92,.19],[s*(w+.11),.92,.38]],.038,0x69636e,4,10);
      L([[s*(w+.12),.96,-.17],[s*(w+.12),.965,.18],[s*(w+.11),.955,.34]],.051,0x847481,5,10);
      B(s*(w+.12),.994,-.025,.095,.019,.19,0x22242d,7);
      for(let j=0;j<4;j++)B(s*(w+.12),1.008,-.10+j*.054,.048,.008,.027,[0xa3bdc9,0xe4bda1,0x99a5b6,0xc19ba9][j],8);
    }
    return {shape:'contoured-seat',rows,cols};
  },
  flightIsland(api){
    const {box,plane,tube}=api;
    const N=46,
      z=x=>-3.24+.24*(x/2.45)**2;
    const bottomFront=[],handRail=[],lowerRail=[],upperGlass=[];
    for(let i=0;i<N;i++){
      const x0=-2.67+i*5.34/N,x1=-2.67+(i+1)*5.34/N;
      const z0=z(x0),z1=z(x1),
            back0=z0+.46,back1=z1+.46,
            face0=z0+.43,face1=z1+.43,
            fwd0=z0-.53,fwd1=z1-.53;
      // One continuous, slightly swept body. Side faces and tablet slopes meet
      // at matching longitudinal seams; no visible row of repeated cubes.
      plane([x0,.26,back0],[x1,.26,back1],[x1,.94,face1],[x0,.94,face0],0xbeb3aa,2);
      plane([x0,.94,face0],[x1,.94,face1],[x1,1.16,fwd1],[x0,1.16,fwd0],0x292831,7);
      plane([x0,.22,fwd0],[x1,.22,fwd1],[x1,1.16,fwd1],[x0,1.16,fwd0],0x978b8b,3);
      plane([x0,.21,back0],[x1,.21,back1],[x1,.26,back1],[x0,.26,back0],0x5c5763,4);
      if(i%7===0){
        const x=x0,zf=z(x);
        box(x,.46,zf+.455,.027,.35,.038,0x887d83,3);
        box(x,.36,zf+.481,.021,.06,.020,0xc2aca1,4);
      }
      bottomFront.push([x0,.26,back0]);
      handRail.push([x0,.985,face0]);
      lowerRail.push([x0,.32,back0+.010]);
      upperGlass.push([x0,1.175,fwd0]);
    }
    bottomFront.push([2.67,.26,z(2.67)+.46]);
    handRail.push([2.67,.985,z(2.67)+.43]);
    lowerRail.push([2.67,.32,z(2.67)+.47]);
    upperGlass.push([2.67,1.175,z(2.67)-.53]);
    tube(handRail,.022,0xbca89b,4,9);
    tube(lowerRail,.021,0x666775,3,9);
    tube(upperGlass,.028,0x9b92a2,4,9);
    for(let s of [-1,1]){
      const x=s*2.68;
      plane([x,.25,z(x)+.46],[x,1.,z(x)+.43],[x,1.16,z(x)-.53],[x,.24,z(x)-.53],0xaaa39f,2);
      box(x,.23,z(x)+.03,.20,.045,.47,0x777582,3);
    }
    // The six separately mapped touch surfaces are still owned by the original
    // bridge code; this body leaves their exact coordinates and UVs unchanged.
    return {shape:'continuous-curved-flight-desk',segments:N};
  }
});