'use client'
//================ IMPORTS ================//
import { useState, useEffect } from 'react'
import { Bell, Trash2 } from 'lucide-react'
import { format, formatDistanceToNow } from 'date-fns'
import { useAuth } from '@/app/contexts/AuthContext'
import {
  Popover,
  PopoverContent,
  PopoverTrigger
} from '@/components/ui/popover'
import { ScrollArea } from '@/components/ui/scroll-area'
import { toast } from 'sonner'
import { supabase } from '@/Clients/supabase/client'
import Cookies from 'js-cookie'
import CustomButton from '@/components/ui/custom-button'

//================ COMPONENT ================//
const NotificationsButton = ({ iconSize = 20 }) => {
  //================ STATE & HOOKS ================//
  const { user, notifications, setNotifications } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [localNotifications, setLocalNotifications] = useState(
    notifications || []
  )
  const [now, setNow] = useState(new Date())

  //================ EFFECTS ================//
  useEffect(() => {
    if (!user) return

    const fetchNotifications = async () => {
      try {
        const { data, error } = await supabase
          .from('user_data')
          .select('notifications')
          .eq('uuid', user.uuid)
          .single()

        if (error) {
          console.error('Error fetching notifications:', error)
          return
        }

        if (data?.notifications) {
          let notificationsData = data.notifications
          if (typeof notificationsData === 'string') {
            try {
              notificationsData = JSON.parse(notificationsData)
            } catch (e) {
              console.error('Failed to parse notifications JSON:', e)
              notificationsData = []
            }
          }

          if (Array.isArray(notificationsData)) {
            setNotifications(notificationsData)
            setLocalNotifications(notificationsData)
          } else {
            setNotifications([])
            setLocalNotifications([])
          }
        }
      } catch (err) {
        console.error('Failed to fetch notifications:', err)
      }
    }

    fetchNotifications()
  }, [user, setNotifications])

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date())
    }, 60 * 1000) // Update every minute

    return () => {
      clearInterval(timer)
    }
  }, [])

  //================ HELPERS ================//
  // Format the notification time
  const formatNotificationTime = timestamp => {
    try {
      const date = new Date(timestamp)

      if (now.getTime() - date.getTime() < 24 * 60 * 60 * 1000) {
        return formatDistanceToNow(date, { addSuffix: true })
      }

      return format(date, "MMM d, yyyy 'at' h:mm a")
    } catch (error) {
      console.error('Error formatting time:', error, timestamp)
      return 'Unknown time'
    }
  }

  const updateUserData = async updatedNotifications => {
    if (!user) return
    setIsDeleting(true)
    try {
      const { error } = await supabase
        .from('user_data')
        .update({ notifications: updatedNotifications })
        .eq('uuid', user.uuid)

      if (error) {
        console.error('Error updating notifications:', error)
        toast.error('Failed to delete notification')
        setIsDeleting(false)
        return false
      }

      setNotifications(updatedNotifications)
      const updatedUser = { ...user, notifications: updatedNotifications }
      Cookies.set('user_data', JSON.stringify(updatedUser))
      if (Cookies.get('fallback_user_data')) {
        Cookies.set('fallback_user_data', JSON.stringify(updatedUser))
      }
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(updatedUser))
      }
      setIsDeleting(false)
      return true
    } catch (err) {
      console.error('Failed to update notifications:', err)
      toast.error('Failed to delete notification')
      setIsDeleting(false)
      return false
    }
  }

  const unreadCount = (
    Array.isArray(localNotifications) ? localNotifications : []
  ).filter(notification => !notification.read).length

  //================ HANDLERS ================//
  const handleDeleteNotification = async id => {
    if (isDeleting) return
    const updatedNotifications = (
      Array.isArray(localNotifications) ? localNotifications : []
    ).filter(notification => notification.id !== id)
    const success = await updateUserData(updatedNotifications)
    if (success) {
      toast.success('Notification deleted')
      setLocalNotifications(updatedNotifications)
    }
  }

  const handleClearAll = async () => {
    if (isDeleting || !localNotifications?.length) return
    const success = await updateUserData([])
    if (success) {
      toast.success('All notifications cleared')
      setLocalNotifications([])
      setIsOpen(false)
    }
  }

  const markAsRead = async id => {
    if (isDeleting) return
    const updatedNotifications = (
      Array.isArray(localNotifications) ? localNotifications : []
    ).map(notification =>
      notification.id === id ? { ...notification, read: true } : notification
    )
    const success = await updateUserData(updatedNotifications)
    if (success) {
      setLocalNotifications(updatedNotifications)
    }
  }

  //================ RENDER ================//
  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <CustomButton
          variant='outline'
          className=' w-auto items-center space-x-2 rounded-full bg-tekk-darkest  text-white px-4 py-2 text-sm font-medium transition-all flex'
        >
          <Bell size={iconSize} />
          {unreadCount > 0 && (
            <div className=' flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white'>
              {unreadCount > 9 ? '9+' : unreadCount}
            </div>
          )}
        </CustomButton>
      </PopoverTrigger>
      <PopoverContent
        className='w-80 p-0 bg-tekk-darkest border-tekk-dark text-white'
        align='end'
        side='bottom'
      >
        <div className='flex items-center justify-between border-b border-tekk-dark p-4'>
          <h3 className='font-semibold'>Notifications</h3>
          {Array.isArray(localNotifications) && localNotifications.length > 0 && (
            <button
              variant='ghost'
              size='sm'
              className='h-8 px-2 text-xs text-gray-400 hover:text-gray-200 cursor-pointer'
              onClick={handleClearAll}
              disabled={isDeleting}
            >
              Clear All
            </button>
          )}
        </div>
        <div className='overflow-hidden' style={{ maxHeight: '300px' }}>
          <ScrollArea className='h-[300px]'>
            {!Array.isArray(localNotifications) ||
              localNotifications.length === 0 ? (
              <div className='py-6 text-center text-gray-500'>
                <div className='mb-2 flex justify-center'>
                  <Bell className='h-8 w-8 text-gray-300' />
                </div>
                <p className='text-sm'>No notifications to display</p>
              </div>
            ) : (
              <div className='divide-y divide-tekk-dark'>
                {localNotifications.map(notification => (
                  <div
                    key={notification.id}
                    className={`relative p-4 transition-all ${!notification.read ? 'bg-tekk-dark ' : ''
                      }`}
                    onClick={() =>
                      !notification.read && markAsRead(notification.id)
                    }
                  >
                    <div className='flex items-start justify-between gap-2'>
                      <div className='flex-1'>
                        <h4 className='text-sm font-medium'>
                          {notification.title}
                        </h4>
                        <p className='mt-1 text-xs text-gray-300'>
                          {notification.message}
                        </p>
                        <p className='mt-1.5 text-xs text-gray-400'>
                          {formatNotificationTime(notification.time)}
                        </p>
                      </div>
                      <button
                        variant='ghost'
                        size='icon'
                        className='h-6 w-6 cursor-pointer text-red-500 hover:text-red-700'
                        onClick={e => {
                          e.stopPropagation()
                          handleDeleteNotification(notification.id)
                        }}
                        disabled={isDeleting}
                      >
                        <Trash2 className='h-3.5 w-3.5' />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
      </PopoverContent>
    </Popover>
  )
}

//================ EXPORTS ================//
export default NotificationsButton
