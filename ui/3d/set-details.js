/* USS Asteria / Bridge — original set-dressing geometry, room 01.
   Pure additive geometry. The approved walking controls and canonical room graph
   are owned by index.html; this module does not touch campaign state. */
'use strict';
window.AsteriaSetDetails=function buildAsteriaSetDetails(api){
  const {box,roundBox,cyl,ellipse,ring,tube,plane,radial,arc,surface,wallPos,W,D}=api;
  const C={linen:0xd1c4b7,pearl:0xe5d8c9,shadow:0x504b56,satin:0xb4a9a9,gunmetal:0x30323b,
    bronze:0xb59a83,copper:0xa67f70,plum:0x7d6676,mulberry:0x8e788b,steel:0x89949f,
    cyan:0x97bfce,ivory:0xf5e0c7,light:0xdcecf6,black:0x151923,deep:0x282831,
    marine:0x5e6977,matte:0x8a8791};
  let pieces=0;
  const B=(...args)=>{pieces++;box(...args)};
  const R=(...args)=>{pieces++;roundBox(...args)};
  const L=(...args)=>{pieces++;tube(...args)};
  const Ell=(...args)=>{pieces++;ellipse(...args)};
  const Cyl=(...args)=>{pieces++;cyl(...args)};
  const Rad=(...args)=>{pieces++;radial(...args)};
  const PI=Math.PI;
  const seeded=n=>{let x=Math.sin(n*93.719+17.331)*43758.5453123;return x-Math.floor(x)};
  // Millimetre-scale floor joints, walk-off mats, inset grilles, weighted contact shadows.
  const contacts=[[-1.15,-2.22,.53,.68],[1.15,-2.22,.53,.68],[3.88,-1.05,.44,.59],
    [-3.33,4.12,.64,.61],[3.33,4.12,.64,.61],[0,1.15,.81,1.00]];
  contacts.forEach(([x,z,rx,rz])=>Ell(x,.038,z,rx,rz,0x484851,1,42));
  for(let side of [-1,1]){
    // Directional carpeting seams avoid the toy-like uniform flooring.
    for(let j=0;j<15;j++){
      const a=(j+1)*PI/17;
      const x=side*Math.sin(a)*5.50,z=Math.cos(a)*4.75;
      if(Math.abs(z)>3.65 && Math.abs(x)<1.9)continue;
      L([[x*.93,.044,z*.93],[x,.044,z]],.006,0x64646f,1,4);
    }
    for(let j=0;j<11;j++){
      const x=side*(4.45+j*.21);
      B(x,.055,-4.82,.012,.008,.50,j%3===0?C.bronze:0x6b6b7b,4);
    }
  }
  for(let j=0;j<26;j++){
    const x=(j-12.5)*.084;
    B(x,.031,5.65,.045,.009,.22,j%3===0?C.steel:C.gunmetal,3);
    B(x,.040,5.70,.038,.008,.035,C.shadow,7);
  }
  // Rounded, laminated vertical acoustic wall bays. Each wall bay has an inner relief,
  // machined edge, inset kick line and fasteners. Do not cover the bridge screen/doors.
  for(let k=0;k<64;k++){
    const a=(k+.50)*2*PI/64;
    const front=Math.abs(a)>PI-.58, aft=Math.abs(a)<.20, leftDoor=Math.abs(Math.abs(a)-PI/2)<.22;
    if(front||aft||leftDoor)continue;
    const wall=wallPos(a,.957);const tangent=[Math.cos(a),-Math.sin(a)];
    const p=(dx,y)=>[wall[0]+tangent[0]*dx,y,wall[1]+tangent[1]*dx];
    const p0=p(-.265,.72),p1=p(.265,.72),p2=p(.265,2.91),p3=p(-.265,2.91);
    plane(p0,p1,p2,p3,k%7===0?0xaaa1a2:C.linen,2);
    Rad(a,.955,.47,.79,.813,C.shadow,3);
    Rad(a,.955,.47,2.84,2.868,0xbaa994,4);
    Rad(a,.953,.042,.81,2.84,k%4===0?0x766a72:0xaca2a0,3);
    const a2=a+.032;
    Rad(a2,.952,.015,.93,2.78,0x6d6670,3);
    for(let y of [.94,2.73]){
      const pp=p(.224,y);
      B(pp[0],y,pp[2],.028,.026,.028,0x928786,4);
      B(pp[0],y+.003,pp[2],.009,.007,.009,C.black,7);
    }
    if(k%5===0){
      const x=wall[0]*.984,z=wall[1]*.984;
      Cyl(x,.23,z,.026,.026,.32,C.gunmetal,3,8);
      Cyl(x,.30,z,.023,.023,.047,C.ivory,8,8);
    }
  }
  // Upright structural ribs at shallow circular angles; cast floor-to-wall relief.
  for(let k=0;k<36;k++){
    const a=k*2*PI/36;
    if(Math.abs(a)<.20||Math.abs(Math.abs(a)-PI)<.54||Math.abs(Math.abs(a)-PI/2)<.20)continue;
    Rad(a,.944,.082,.53,3.62,C.steel,3);
    Rad(a,.932,.025,.58,3.56,C.satin,4);
  }
  // Under-panel service shelves & concealed floor air-exchange grilles.
  for(let side of [-1,1])for(let j=0;j<18;j++){
    const a=side*(.40+j*.125);
    if(Math.abs(a-PI/2)<.20||Math.abs(a+PI/2)<.20)continue;
    const v=wallPos(a,.946);
    B(v[0],.36,v[1],.048,.24,.11,j%4===0?C.steel:C.gunmetal,3,a);
    B(v[0],.19,v[1],.039,.013,.11,C.shadow,4,a);
  }
  // Physical cove lighting, not neon trim: warm polycarbonate diffusers in dark housings.
  for(let s of [-1,1])for(let j=0;j<5;j++){
    const a=s*(.39+j*.43);
    if(Math.abs(Math.abs(a)-PI/2)<.19)continue;
    const c=wallPos(a,.920),t=[Math.cos(a),-Math.sin(a)];
    const end=(dx,y)=>[c[0]+t[0]*dx,y,c[1]+t[1]*dx];
    L([end(-.27,3.30),end(.27,3.30)],.045,C.deep,7,8);
    L([end(-.215,3.277),end(.215,3.277)],.025,0xdce5e6,8,8);
    for(let h of [.90,1.68,2.46]){
      const e=wallPos(a,.912);
      B(e[0],h,e[1],.06,.024,.058,C.steel,3,a);
    }
  }
  // Ceiling acoustic baffles, suspended longitudinal uplight coffers and access fasteners.
  for(let s of [-1,1]){
    for(let k=0;k<4;k++){
      const z=-3.30+k*1.72,x=s*4.92;
      B(x,3.845,z,.64,.045,.48,0x67646c,3);
      B(x,3.818,z,.48,.016,.31,0xb6c1c7,8);
    }
    // Paired stepped columns beside viewer — read as actual built scenery.
    for(let i=0;i<7;i++){
      const z=-5.68+i*.18;
      B(s*(3.36+i*.035),2.14,z,.065,2.34,.055,0xa79c99,3);
    }
  }
  for(let i=0;i<14;i++){
    const a=i*2*PI/14;
    const x=Math.sin(a)*2.02,z=Math.cos(a)*1.62;
    Cyl(x,4.318,z,.046,.046,.025,C.bronze,4,12);
  }
  // The display has a realistic laminated seal and segmented frame joinery.
  for(let s of [-1,1]){
    B(s*3.16,2.015,-6.023,.046,2.43,.035,C.black,7);
    B(s*3.18,2.012,-6.012,.014,2.29,.02,C.steel,4);
    for(let j=0;j<13;j++)B(s*3.47,.98+j*.182,-5.90,.034,.052,.036,j%5===0?C.copper:C.steel,4);
  }
  B(0,3.22,-6.008,6.34,.035,.026,C.black,7);
  B(0,.80,-6.008,6.34,.038,.025,C.black,7);
  B(0,3.29,-6.005,6.28,.016,.024,0xb4c0c6,8);
  for(let j=0;j<17;j++)B((j-8)*.362,.68,-5.92,.12,.018,.025,j%6===0?C.ivory:C.steel,8);
  // Captain's platform has bevelled lower extrusion, curved gasket, tenoned rail hardware.
  for(let j=0;j<18;j++){
    const a=j*2*PI/18,x=Math.sin(a)*1.87,z=1.11+Math.cos(a)*1.565;
    if(j%3===0)Cyl(x,.165,z,.017,.017,.09,C.shadow,4,8);
    if(j%2===0)B(x,.284,z,.031,.011,.025,0x877d83,4,-a);
  }
  Ell(0,.304,1.11,1.48,1.16,0x655d6b,1,70);
  for(let s of [-1,1]){
    // Structural supports on the inset bridge chair, suede side panels, stitches and arm electronics.
    B(s*.39,.64,1.42,.115,.35,.43,0x686170,3);
    B(s*.390,.88,1.53,.082,.16,.095,C.shadow,3);
    for(let j=0;j<11;j++)B(s*.376,1.06+j*.062,1.700,.037,.012,.008,0xcab9b2,4);
    for(let j=0;j<7;j++)B(s*.31,1.1+j*.099,1.782,.015,.014,.014,0xb4a3a4,4);
    for(let j=0;j<10;j++){
      const z=.97-j*.057;
      B(s*.39,1.020,z,.103,.008,.024,j%4===0?0xc0b0bc:C.plum,4);
    }
    B(s*.51,.925,1.08,.12,.045,.57,C.steel,4);
    B(s*.51,.964,1.078,.092,.014,.46,C.black,7);
    for(let j=0;j<6;j++)B(s*.51,.976,.89+j*.072,.06,.008,.03,[C.cyan,C.ivory,C.plum][j%3],8);
    // Captain's two autonomous data pylons: undercut edges, screw fittings and tactile strips.
    const x=s*1.27;
    B(x,1.138,.50,.71,.02,.78,C.gunmetal,4,s*.22);
    B(x,.425,.605,.55,.028,.84,0x948987,3,s*.22);
    for(let j=0;j<8;j++){
      const zz=.16+j*.10;
      B(x+s*.20,1.18,zz,.046,.018,.04,j%3===0?C.cyan:C.bronze,8,s*.22);
    }
    for(let j=0;j<3;j++)B(x+s*.33,.60+j*.19,.64,.025,.06,.12,0x6c6165,3,s*.22);
  }
  // Flight island: seam-capped individual console cassettes, handrails, raised
  // tactile keys, tiny instrument lenses, cantilever toe clearance and trim.
  for(let j=0;j<11;j++){
    const x=(j-5)*.48,z=-3.24+.24*(x/2.45)**2;
    const r=Math.atan2(.18*x,1);
    B(x,1.061,z-.08,.50,.021,1.01,C.gunmetal,7,r);
    B(x,1.08,z+.405,.47,.018,.035,0x7b7a88,4,r);
    B(x,1.065,z-.51,.46,.017,.03,C.steel,4,r);
    for(let k=0;k<4;k++){
      const dx=(k-1.5)*.086;
      B(x+dx,1.098,z+.345,.061,.008,.028,k%3===0?C.ivory:0x637988,8,r);
    }
    B(x,.225,z+.14,.44,.04,.56,0x75747f,3,r);
  }
  for(let s of [-1,1]){
    // Luminescent practical under-desk strip and structural braces.
    L([[s*.14,.38,-3.69],[s*1.26,.38,-3.73],[s*2.52,.38,-3.52]],.023,C.ivory,8,8);
    for(let i=0;i<9;i++){
      const x=s*(.23+i*.29),z=-3.05+.1*(x/2.5)**2;
      const y=1.132;
      B(x,y,z+.27,.06,.013,.027,i%3===0?C.cyan:C.matte,8);
      B(x,y,z+.32,.08,.013,.021,i%4===0?C.copper:C.pearl,8);
    }
    // Seat details for two pilots (not an Enterprise-style 3-seat command cluster).
    B(s*1.14,.56,-2.13,.41,.07,.18,C.gunmetal,4);
    B(s*1.14,.83,-1.84,.43,.024,.05,C.bronze,4);
    for(let k=0;k<4;k++)B(s*1.14,.89+k*.145,-1.73+k*.014,.42,.018,.022,0xb4a1a7,4);
  }
  // Aft gallery: 3-D shelf reveals, hand-rest rails, latching inspection panels,
  // panel underside reflections and instrument indicator boxes.
  for(let s of [-1,1]){
    L([[s*1.87,.63,3.69],[s*3.6,.63,3.68],[s*5.30,.63,3.79]],.031,0xb5a99c,4,8);
    L([[s*1.88,.79,3.70],[s*3.58,.79,3.71],[s*5.25,.79,3.82]],.021,C.steel,3,8);
    for(let j=0;j<13;j++){
      const x=s*(2.0+j*.255);
      B(x,.40,3.90,.19,.054,.058,j%4===0?C.ivory:C.gunmetal,j%4===0?8:7);
      B(x,.27,4.93,.12,.13,.025,0x858089,3);
      B(x,.31,4.94,.035,.027,.027,j%3===0?C.cyan:C.ivory,8);
    }
    // Cable trunking line across aft pedestal service faces.
    B(s*3.5,.315,5.112,3.15,.021,.031,C.bronze,4,s*.09);
    for(let i=0;i<7;i++)B(s*(2.12+i*.46),.19,5.122,.12,.012,.035,i%2?C.shadow:C.steel,4);
  }
  // Aft corridor doorway — only verified portal; thick jambs, useful wayfinding
  // illumination, raised access code fixtures (side doors remain scenery only).
  for(let s of [-1,1]){
    B(s*1.04,1.6,6.055,.095,2.70,.076,0x35323b,7);
    B(s*1.090,1.64,6.004,.024,2.54,.025,C.steel,4);
    B(s*.75,3.06,6.020,.62,.045,.032,0xc1b4ae,4);
    B(s*.72,.225,6.029,.57,.042,.043,C.shadow,3);
    for(let j=0;j<8;j++)B(s*1.187,.61+j*.20,6.021,.045,.11,.04,j%4===0?C.ivory:C.cyan,8);
  }
  // Readable at a glance: inset procedural LED status rows across the bridge.
  for(let a of [-2.63,-2.26,-1.23,1.24,2.27,2.64]){
    const p=wallPos(a,.91),t=[Math.cos(a),-Math.sin(a)];
    for(let j=0;j<12;j++){
      const x=p[0]+t[0]*(j-5.5)*.071,z=p[1]+t[1]*(j-5.5)*.071;
      B(x,1.01,z,.055,.022,.022,j%7===0?C.ivory:j%3===0?C.cyan:0x575663,8,a);
    }
  }
  return Object.freeze({pieces,roomId:'AST-D01-BRIDGE'});
};