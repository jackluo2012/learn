'use client'

import Main from '@/components/Main';
import Navbar from '@/components/Navbar';
import SolanaProviders from '@/components/SolanaProviders';
import React from 'react';


export default function Home() {

  return (
    <SolanaProviders>
      <Navbar/>
      <Main/>
    </SolanaProviders>
  )
}
