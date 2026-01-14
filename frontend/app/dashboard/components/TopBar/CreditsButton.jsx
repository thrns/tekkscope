'use client'
//================ IMPORTS ================//
import { Coins, LoaderIcon } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/app/contexts/AuthContext'
import { CreditsProvider, useCredits } from '@/app/contexts/CreditsContext'
import CustomButton from '@/components/ui/custom-button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'

//================ INNER COMPONENT ================//
const CreditsButtonInner = () => {
  //================ STATE & HOOKS ================//
  const { balance, loading, refreshCredits } = useCredits()
  const router = useRouter()

  //================ HELPER ================//
  const fmt = (n) => {
    try { return Number(n).toFixed(2) } catch { return String(n || 0) }
  }

  //================ RENDER ================//
  return (
    <Popover>
      <PopoverTrigger asChild>
        <CustomButton
          variant='outline'
          className=' w-auto items-center space-x-2 rounded-full bg-tekk-darkest  text-white px-4 py-2 text-sm font-medium transition-all flex'
          onClick={() => refreshCredits()}
        >
          <Coins size={18} className='text-tekk-primary' />
          {loading ? (
            <LoaderIcon className='animate-spin h-4 w-4' />
          ) : (
            <span>{fmt(balance)}</span>
          )}
        </CustomButton>
      </PopoverTrigger>
      <PopoverContent
        className='w-64 p-3 bg-tekk-darkest border-tekk-dark text-white'
        align='end'
        side='bottom'
      >
        <div className='text-xs text-white/70 mb-2'>Current balance</div>
        <div className='text-lg font-medium mb-3'>{fmt(balance)}</div>
        <button
          type='button'
          className='w-full rounded-md bg-tekk-primary text-black px-3 py-2 text-sm'
          onClick={() => router.push('/pricing')}
        >
          Get more credits
        </button>
      </PopoverContent>
    </Popover>
  )
}

//================ MAIN COMPONENT ================//
const CreditsButton = () => {
  const { user } = useAuth()
  return (
    <CreditsProvider userId={user?.id}>
      <CreditsButtonInner />
    </CreditsProvider>
  )
}

//================ EXPORTS ================//
export default CreditsButton
